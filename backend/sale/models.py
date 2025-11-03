from decimal import Decimal
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
import uuid

from people.models import Customer, Seller
from catalog.models import Product, Promotion
from stock.models import StockMovement
from stock.models import Stock
from payment.models import PaymentMethod, Receivable, PaymentEvent
from cashier.models import CashierSession, CashMovement


ORDER_STATUS = (
    ("DRAFT", "DRAFT"),
    ("CONFIRMED", "CONFIRMED"),
    ("CANCELLED", "CANCELLED"),
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Order(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    seller = models.ForeignKey(Seller, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=12, choices=ORDER_STATUS, default="DRAFT", db_index=True)
    # Tipo de pedido: 'carrinho' (padrão) ou 'orcamento'
    order_type = models.CharField(max_length=16, default="carrinho", db_index=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    # Subtotal before any order-level discounts (sum of unit_price * quantity)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    # Absolute discount applied at order level (currency value)
    order_discount_abs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payment_method = models.ForeignKey(PaymentMethod, null=True, blank=True, on_delete=models.PROTECT, related_name="orders")
    # Additional payment metadata (method name, type, installments, fee percent, etc.)
    payment_metadata = models.JSONField(null=True, blank=True)
    # Computed fee amount (absolute) charged by payment method at confirm time
    payment_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    # Número de pedido de venda (gerado na confirmação): formato YYYYMMDD-HHMM
    sales_order = models.CharField(max_length=20, blank=True, null=True, unique=True, db_index=True)

    def clean(self):
        # Prevent changing payment_method after confirmation
        if self.pk:
            try:
                prev = Order.objects.get(pk=self.pk)
            except Order.DoesNotExist:
                prev = None
            if prev and prev.status != "DRAFT" and prev.payment_method_id != self.payment_method_id:
                raise ValidationError({"payment_method": "Não é permitido alterar o método de pagamento após confirmação."})

    def recalc_totals(self):
        # Compute subtotal (sum of unit_price * quantity), item-level discounts and line totals
        subtotal = Decimal("0.00")
        items_discount = Decimal("0.00")
        line_total_sum = Decimal("0.00")
        for it in self.items.all():
            subtotal += (it.unit_price or Decimal("0.00")) * (it.quantity or Decimal("0.00"))
            items_discount += (it.discount_value or Decimal("0.00"))
            line_total_sum += (it.line_total or Decimal("0.00"))

        # Apply order-level absolute discount after item discounts
        order_disc = (self.order_discount_abs or Decimal("0.00"))
        total_after_items = line_total_sum
        total_after_order_discount = total_after_items - order_disc
        if total_after_order_discount < Decimal("0.00"):
            total_after_order_discount = Decimal("0.00")

        # discount_total should reflect both item-level discounts and order-level absolute discount
        total_discount = items_discount + order_disc

        self.subtotal = subtotal
        self.total = total_after_order_discount
        self.discount_total = total_discount
        self.save(update_fields=["subtotal", "total", "discount_total", "updated_at"])

    def __str__(self):
        so = f" #{self.sales_order}" if self.sales_order else ""
        return f"Order{so} ({self.status})"


class OrderItem(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def clean(self):
        errors = {}
        if self.quantity is None or self.quantity <= 0:
            errors["quantity"] = "Quantidade deve ser positiva."
        if errors:
            raise ValidationError(errors)

    def compute_pricing(self):
        base_price = Decimal(str(self.unit_price))
        # Determine promotion discount
        promo = None
        manual_discount = Decimal(str(self.discount_percent or 0))
        promo_discount = Decimal("0")
        # Find current promotion
        promo = self.product.promotions.filter(active=True).first()
        if promo and promo.is_current:
            promo_discount = Decimal(str(promo.percent_off or 0))
        # Seller manual discount cap
        cap = Decimal(str(self.order.seller.discount_max or 0))
        manual_capped = min(manual_discount, cap)
        # Single best policy: choose higher between promotion and manual_capped
        best_discount = promo_discount if promo_discount >= manual_capped else manual_capped
        # Price floor: cost + MIN_MARGIN_PERCENT
        min_margin = Decimal(str(getattr(settings, "MIN_MARGIN_PERCENT", 0)))
        min_price = Decimal(str(self.product.cost_price)) * (Decimal("1.0") + (min_margin / Decimal("100")))

        discounted = base_price * (Decimal("1.0") - (best_discount / Decimal("100")))
        if discounted < min_price:
            # Adjust discount so final price equals min_price
            if base_price <= 0:
                eff_discount = Decimal("0")
            else:
                eff_discount = (Decimal("1.0") - (min_price / base_price)) * Decimal("100")
                if eff_discount < 0:
                    eff_discount = Decimal("0")
            best_discount = max(Decimal("0"), eff_discount)
            discounted = max(min_price, discounted)

        self.discount_percent = best_discount.quantize(Decimal("0.01"))
        self.discount_value = (base_price * (self.discount_percent / Decimal("100"))).quantize(Decimal("0.01"))
        self.line_total = (discounted * Decimal(str(self.quantity))).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        self.full_clean()
        self.compute_pricing()
        super().save(*args, **kwargs)
        self.order.recalc_totals()

    def __str__(self):
        return f"Item {self.product_id} x {self.quantity}"


@transaction.atomic
def confirm_order(order: Order):
    if order.status != "DRAFT":
        raise ValidationError("Somente pedidos em rascunho podem ser confirmados.")
    if not order.payment_method:
        raise ValidationError("Selecione o método de pagamento antes de confirmar.")
    # Enforce open cashier for cash payments if configured
    if getattr(settings, "CASHIER_REQUIRED_FOR_SALE", True) and order.payment_method.type == "cash":
        sess = CashierSession.objects.filter(status="OPEN").order_by("-opened_at").first()
        if not sess:
            raise ValidationError("É necessário um caixa aberto para confirmar venda em dinheiro.")
    # Stock availability check


    for item in order.items.select_related("product"):
        try:
            st = Stock.objects.select_for_update().get(product=item.product)
        except Stock.DoesNotExist:
            st = None
        if getattr(settings, "BLOCK_SALE_IF_ZERO_STOCK", True):
            if not st or st.quantity_current <= 0:
                raise ValidationError(f"Produto sem estoque: {item.product.name}")
        if getattr(settings, "PREVENT_NEGATIVE_STOCK", True):
            if st and st.quantity_current - item.quantity < 0:
                raise ValidationError(f"Estoque insuficiente para {item.product.name}")

    # Apply stock movements
    for item in order.items.all():
        StockMovement.objects.create(
            product=item.product,
            type="SAIDA",
            quantity=item.quantity,
            reference=f"ORDER {order.id}",
        )

    # Create receivable for the order total using selected payment method
    logger = logging.getLogger("sale.payment")
    pm = order.payment_method
    # Log payment metadata for debugging fee_percent
    try:
        logger.info("[sale] payment_metadata for order=%s: %s", order.id, order.payment_metadata)
    except Exception:
        pass
    from datetime import date, timedelta
    due = date.today() + timedelta(days=int(pm.settlement_days or 0))
    Receivable.objects.create(
        method=pm,
        reference=f"ORDER {order.id}",
        due_date=due,
        amount=order.total,
    )
    # Compute fee amount based on stored metadata (prefer metadata fee_percent) or payment method
    try:
        fee_pct = None
        if order.payment_metadata and isinstance(order.payment_metadata, dict) and order.payment_metadata.get('fee_percent') is not None:
            fee_pct = Decimal(str(order.payment_metadata.get('fee_percent') or 0))
        else:
            fee_pct = Decimal(str(pm.fee_percent or 0))
        fee_fixed = Decimal(str(getattr(pm, 'fee_fixed', 0) or 0))
        # Prefer explicit absolute fee_value when provided by frontend
        fee = None
        if order.payment_metadata and isinstance(order.payment_metadata, dict) and order.payment_metadata.get('fee_value') is not None:
            try:
                fee = Decimal(str(order.payment_metadata.get('fee_value') or 0))
            except Exception:
                fee = None
        if fee is None:
            fee = (order.total * (fee_pct or Decimal('0')) / Decimal('100')) + fee_fixed
        order.payment_fee = fee.quantize(Decimal('0.01'))
        order.save(update_fields=['payment_fee'])
    except Exception:
        order.payment_fee = Decimal('0.00')
        try: order.save(update_fields=['payment_fee'])
        except Exception: pass
    logger.info("[sale] receivable created order=%s method=%s amount=%s due=%s", order.id, pm.code, order.total, due)
    # Auto-settle for immediate methods (e.g., settlement_days=0)
    rec = Receivable.objects.filter(reference=f"ORDER {order.id}", method=pm).first()
    if getattr(pm, "auto_settle", False) and rec and rec.amount > 0:
        from datetime import date
        # Calculate optional fees
        fee = (rec.amount * (pm.fee_percent or 0) / Decimal("100")) + (pm.fee_fixed or Decimal("0"))
        evt = PaymentEvent.objects.create(
            receivable=rec,
            amount=rec.amount,
            fee_amount=Decimal(str(fee)),
            paid_date=date.today(),
            external_id=f"AUTO-ORDER-{order.id}",
            metadata={"auto": True},
        )
        evt.apply()
        logger.info("[sale] receivable auto-settled order=%s method=%s amount=%s fee=%s", order.id, pm.code, rec.amount, fee)
        # For cash payments, record cash inflow in current session
        if pm.type == "cash":
            sess = CashierSession.objects.filter(status="OPEN").order_by("-opened_at").first()
            if sess:
                CashMovement.objects.create(session=sess, type="INFLOW", amount=order.total, reason="SALE", reference=f"ORDER {order.id}")

    from django.utils import timezone
    order.status = "CONFIRMED"
    # Gerar número de pedido se ainda não definido
    if not order.sales_order:
        now = timezone.localtime(timezone.now())
        order.sales_order = now.strftime("%Y%m%d-%H%M")
    order.save(update_fields=["status", "sales_order", "updated_at"])


@transaction.atomic
def cancel_order(order: Order):
    if order.status != "CONFIRMED":
        raise ValidationError("Somente pedidos confirmados podem ser cancelados.")
    # Revert stock
    for item in order.items.all():
        StockMovement.objects.create(
            product=item.product,
            type="ENTRADA",
            quantity=item.quantity,
            reference=f"ORDER_CANCEL {order.id}",
        )
    order.status = "CANCELLED"
    order.save(update_fields=["status", "updated_at"])
