from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('polera', 'Polera'),
        ('pantalon', 'Pantalón/Short'),
        ('accesorio', 'Accesorio'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0, help_text="Orden de aparición en el catálogo")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    precio = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True, help_text="Desmarcar para ocultar del catálogo")
    destacado = models.BooleanField(default=False, help_text="Mostrar en página principal")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campos específicos para pantalones
    tipo_pantalon = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        choices=[('short', 'Short'), ('pantalon_largo', 'Pantalón Largo'), ('jogger', 'Jogger')],
        help_text="Solo para pantalones/shorts"
    )
    
    # Campos específicos para accesorios (no usan tallas)
    material = models.CharField(max_length=100, blank=True, null=True, help_text="Solo para accesorios")
    dimensiones = models.CharField(max_length=100, blank=True, null=True, help_text="Solo para accesorios")
    stock_accesorio = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Stock para accesorios (no tienen tallas)"
    )
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-destacado', '-fecha_creacion']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nombre
    
    @property
    def tiene_stock(self):
        """Verifica si hay stock disponible"""
        if self.categoria.tipo == 'accesorio':
            return self.stock_accesorio > 0
        else:
            return self.stock_tallas.filter(cantidad__gt=0).exists()
    
    @property
    def stock_total(self):
        """Retorna stock total del producto"""
        if self.categoria.tipo == 'accesorio':
            return self.stock_accesorio
        else:
            return sum(st.cantidad for st in self.stock_tallas.all())
    
    @property
    def precio_formateado(self):
        return f"${self.precio:,.0f}"
    
    def get_whatsapp_url(self, talla=None):
        """Genera URL de WhatsApp con mensaje predefinido"""
        mensaje = f"Hola! Estoy interesado en: *{self.nombre}*\n"
        mensaje += f"Precio: ${self.precio:,.0f}\n"
        
        if talla:
            mensaje += f"Talla: {talla}\n"
        if self.tipo_pantalon:
            mensaje += f"Tipo: {self.get_tipo_pantalon_display()}\n"
        
        mensaje += f"\n¿Está disponible?"
        
        import urllib.parse
        mensaje_encoded = urllib.parse.quote(mensaje)
        
        return f"https://wa.me/56978605581?text={mensaje_encoded}"


class StockTalla(models.Model):
    """Modelo para gestionar stock individual por talla"""
    TALLA_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stock_tallas')
    talla = models.CharField(max_length=3, choices=TALLA_CHOICES)
    cantidad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cantidad disponible de esta talla"
    )
    
    class Meta:
        verbose_name = "Stock por Talla"
        verbose_name_plural = "Stock por Tallas"
        unique_together = ['producto', 'talla']
        ordering = ['talla']
    
    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla}: {self.cantidad} unidades"
    
    @property
    def estado_stock(self):
        """Retorna el estado del stock para visualización"""
        if self.cantidad == 0:
            return 'sin_stock'
        elif self.cantidad <= 5:
            return 'poco_stock'
        else:
            return 'buen_stock'


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')
    orden = models.IntegerField(default=0, help_text="Orden de aparición en el carrusel")
    es_principal = models.BooleanField(default=False, help_text="Imagen principal del producto")
    
    class Meta:
        verbose_name = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Productos"
        ordering = ['-es_principal', 'orden']
    
    def __str__(self):
        return f"Imagen de {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        if self.es_principal:
            ImagenProducto.objects.filter(producto=self.producto, es_principal=True).update(es_principal=False)
        super().save(*args, **kwargs)