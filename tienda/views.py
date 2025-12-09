from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum
from .models import Producto, Categoria, StockTalla

def get_categorias():
    """Helper para obtener categorías activas"""
    return Categoria.objects.filter(activo=True)

def home(request):
    """Vista principal - home page con productos destacados"""
    productos_destacados = Producto.objects.filter(
        activo=True, 
        destacado=True
    ).prefetch_related('imagenes', 'categoria', 'stock_tallas')[:8]
    
    context = {
        'productos': productos_destacados,
        'categorias': get_categorias(),
    }
    
    return render(request, 'tienda/home.html', context)


def nosotros(request):
    """Vista de la página Nosotros"""
    context = {
        'categorias': get_categorias(),
    }
    
    return render(request, 'tienda/nosotros.html', context)


def catalogo(request):
    """Vista del catálogo completo con filtros"""
    productos = Producto.objects.filter(activo=True).prefetch_related('imagenes', 'categoria', 'stock_tallas')
    
    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    # Filtro por talla
    talla = request.GET.get('talla')
    if talla:
        productos = productos.filter(stock_tallas__talla=talla, stock_tallas__cantidad__gt=0).distinct()
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda)
        )
    
    context = {
        'productos': productos,
        'categorias': get_categorias(),
        'categoria_seleccionada': categoria_id,
        'talla_seleccionada': talla,
        'busqueda': busqueda,
        'tallas': ['S', 'M', 'L', 'XL'],
    }
    
    return render(request, 'tienda/catalogo.html', context)


def producto_detalle(request, slug):
    """Vista de detalle del producto con selector de talla"""
    producto = get_object_or_404(
        Producto.objects.prefetch_related('imagenes', 'stock_tallas').select_related('categoria'),
        slug=slug,
        activo=True
    )
    
    # Obtener imagen principal
    imagen_principal = producto.imagenes.filter(es_principal=True).first()
    if not imagen_principal:
        imagen_principal = producto.imagenes.first()
    
    # Obtener stock por talla (solo para productos que usan tallas)
    stock_por_talla = None
    if producto.categoria.tipo in ['polera', 'pantalon']:
        stock_por_talla = producto.stock_tallas.all()
    
    # Productos relacionados de la misma categoría
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        activo=True
    ).exclude(id=producto.id).prefetch_related('imagenes')[:4]
    
    context = {
        'producto': producto,
        'imagen_principal': imagen_principal,
        'stock_por_talla': stock_por_talla,
        'productos_relacionados': productos_relacionados,
        'categorias': get_categorias(),
    }
    
    return render(request, 'tienda/producto_detalle.html', context)


def categoria_detalle(request, categoria_id):
    """Vista de productos por categoría con filtros funcionales"""
    categoria = get_object_or_404(Categoria, id=categoria_id, activo=True)
    productos = Producto.objects.filter(
        categoria=categoria,
        activo=True
    ).prefetch_related('imagenes', 'stock_tallas')
    
    # Filtro por talla (puede seleccionar múltiples)
    tallas_seleccionadas = request.GET.getlist('talla')
    if tallas_seleccionadas and categoria.tipo in ['polera', 'pantalon']:
        productos = productos.filter(
            stock_tallas__talla__in=tallas_seleccionadas, 
            stock_tallas__cantidad__gt=0
        ).distinct()
    
    # Filtro por precio
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    if precio_min:
        productos = productos.filter(precio__gte=precio_min)
    if precio_max:
        productos = productos.filter(precio__lte=precio_max)
    
    # Ordenamiento
    orden = request.GET.get('orden')
    if orden == 'nombre':
        productos = productos.order_by('nombre')
    elif orden == 'precio_asc':
        productos = productos.order_by('precio')
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio')
    
    context = {
        'categoria': categoria,
        'productos': productos,
        'tallas': ['S', 'M', 'L', 'XL'] if categoria.tipo in ['polera', 'pantalon'] else None,
        'tallas_seleccionadas': tallas_seleccionadas,
        'categorias': get_categorias(),
    }
    
    return render(request, 'tienda/categoria.html', context)