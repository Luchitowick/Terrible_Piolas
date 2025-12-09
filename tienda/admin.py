from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Producto, ImagenProducto, StockTalla

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1
    fields = ['imagen', 'orden', 'es_principal', 'vista_previa']
    readonly_fields = ['vista_previa']
    
    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.imagen.url)
        return "Sin imagen"
    vista_previa.short_description = "Vista Previa"


class StockTallaInline(admin.TabularInline):
    model = StockTalla
    extra = 0
    fields = ['talla', 'cantidad', 'estado_visual']
    readonly_fields = ['estado_visual']
    
    def estado_visual(self, obj):
        if obj.cantidad == 0:
            color = 'red'
            texto = 'SIN STOCK'
        elif obj.cantidad <= 5:
            color = 'orange'
            texto = 'POCO STOCK'
        else:
            color = 'green'
            texto = 'BUEN STOCK'
        return format_html(
            '<span style="color: {}; font-weight: bold; background: {}22; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color, color, texto
        )
    estado_visual.short_description = "Estado"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Solo mostrar para productos que usan tallas
        return qs


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activo', 'cantidad_productos', 'orden']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo', 'orden']
    
    def cantidad_productos(self, obj):
        return obj.productos.count()
    cantidad_productos.short_description = "Productos"
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('activo', 'orden')
        }),
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'categoria', 
        'precio_formateado', 
        'stock_total_display',
        'activo', 
        'destacado',
        'imagen_principal'
    ]
    list_filter = ['categoria', 'activo', 'destacado', 'tipo_pantalon']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo', 'destacado']
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [StockTallaInline, ImagenProductoInline]
    
    def stock_total_display(self, obj):
        stock_total = obj.stock_total
        if stock_total == 0:
            color = 'red'
            texto = 'SIN STOCK'
        elif stock_total <= 10:
            color = 'orange'
            texto = f'{stock_total} unidades'
        else:
            color = 'green'
            texto = f'{stock_total} unidades'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, texto
        )
    stock_total_display.short_description = "Stock Total"
    
    def precio_formateado(self, obj):
        return obj.precio_formateado
    precio_formateado.short_description = "Precio"
    
    def imagen_principal(self, obj):
        imagen = obj.imagenes.filter(es_principal=True).first()
        if not imagen:
            imagen = obj.imagenes.first()
        if imagen:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', imagen.imagen.url)
        return "Sin imagen"
    imagen_principal.short_description = "Imagen"
    
    def get_fieldsets(self, request, obj=None):
        """Muestra campos diferentes según el tipo de categoría"""
        if obj and obj.categoria and obj.categoria.tipo == 'accesorio':
            return (
                ('Información Básica', {
                    'fields': ('nombre', 'slug', 'descripcion', 'categoria', 'precio')
                }),
                ('Detalles del Accesorio', {
                    'fields': ('material', 'dimensiones', 'stock_accesorio'),
                    'description': 'Los accesorios no usan tallas'
                }),
                ('Configuración', {
                    'fields': ('activo', 'destacado')
                }),
            )
        else:
            return (
                ('Información Básica', {
                    'fields': ('nombre', 'slug', 'descripcion', 'categoria', 'precio')
                }),
                ('Detalles del Producto', {
                    'fields': ('tipo_pantalon',),
                    'description': 'El stock por tallas se gestiona abajo en "Stock por Tallas"'
                }),
                ('Configuración', {
                    'fields': ('activo', 'destacado')
                }),
            )
    
    def get_inline_instances(self, request, obj=None):
        """Muestra StockTallaInline solo para productos que usan tallas"""
        inlines = []
        
        if obj:
            if obj.categoria.tipo in ['polera', 'pantalon']:
                inlines.append(StockTallaInline(self.model, self.admin_site))
            inlines.append(ImagenProductoInline(self.model, self.admin_site))
        else:
            inlines.append(ImagenProductoInline(self.model, self.admin_site))
        
        return inlines
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Crear automáticamente registros de stock por talla si es polera o pantalón
        if obj.categoria.tipo in ['polera', 'pantalon']:
            for talla in ['S', 'M', 'L', 'XL']:
                StockTalla.objects.get_or_create(
                    producto=obj,
                    talla=talla,
                    defaults={'cantidad': 0}
                )


@admin.register(StockTalla)
class StockTallaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'talla', 'cantidad', 'estado_visual']
    list_filter = ['producto__categoria', 'talla']
    search_fields = ['producto__nombre']
    list_editable = ['cantidad']
    
    def estado_visual(self, obj):
        if obj.cantidad == 0:
            color = 'red'
            texto = 'SIN STOCK'
        elif obj.cantidad <= 5:
            color = 'orange'
            texto = 'POCO STOCK'
        else:
            color = 'green'
            texto = 'BUEN STOCK'
        return format_html(
            '<span style="color: {}; font-weight: bold; background: {}22; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color, color, texto
        )
    estado_visual.short_description = "Estado"


@admin.register(ImagenProducto)
class ImagenProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'vista_previa', 'es_principal', 'orden']
    list_filter = ['es_principal', 'producto__categoria']
    list_editable = ['orden', 'es_principal']
    
    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.imagen.url)
        return "Sin imagen"
    vista_previa.short_description = "Vista Previa"


admin.site.site_header = "Administración de Tienda Online"
admin.site.site_title = "Tienda Admin"
admin.site.index_title = "Panel de Control"