from sqlalchemy import select
from .models import Category, Product

ITEMS = [
    (
        "portatiles",
        "Portátiles",
        'Portátil de aluminio 14"',
        89900,
        8,
        1450,
        "laptop.jpg",
        "Ligero, silencioso y preparado para una jornada de trabajo. Pantalla de 14 pulgadas, 16 GB de memoria y SSD de 512 GB.",
    ),
    (
        "audio",
        "Audio",
        "Auriculares de estudio",
        12900,
        12,
        280,
        "headphones.jpg",
        "Sonido equilibrado, almohadillas cómodas y cable desmontable para concentrarte en lo que importa.",
    ),
    (
        "perifericos",
        "Periféricos",
        "Teclado mecánico compacto",
        8900,
        15,
        740,
        "keyboard.jpg",
        "Un escritorio más despejado. Distribución compacta y teclas mecánicas con un tacto preciso.",
    ),
    (
        "perifericos",
        "Periféricos",
        "Ratón inalámbrico",
        4900,
        0,
        95,
        "mouse.jpg",
        "Control preciso y diseño cómodo para acompañarte cada día. Actualmente sin existencias.",
    ),
    (
        "pantallas",
        "Pantallas",
        'Monitor de escritorio 27"',
        24900,
        6,
        4200,
        "monitor.jpg",
        "Más espacio para tus ideas. Pantalla de 27 pulgadas y una base estable para tu escritorio.",
    ),
    (
        "accesorios",
        "Accesorios",
        "Reloj de diseño",
        7900,
        9,
        60,
        "watch.jpg",
        "Una pieza sencilla para completar tu día: esfera limpia, correa cómoda y construcción ligera.",
    ),
    (
        "portatiles",
        "Portátiles",
        'Portátil creativo 16"',
        139900,
        4,
        2100,
        "laptop.jpg",
        "Una pantalla amplia para diseño y desarrollo. Memoria de 32 GB y almacenamiento SSD de 1 TB.",
    ),
    (
        "audio",
        "Audio",
        "Auriculares esenciales",
        5900,
        20,
        210,
        "headphones.jpg",
        "Un compañero para trabajar, estudiar y escuchar tus listas favoritas sin complicaciones.",
    ),
    (
        "perifericos",
        "Periféricos",
        "Teclado de trabajo",
        6900,
        10,
        650,
        "keyboard.jpg",
        "Una herramienta de uso diario con diseño cuidado y una superficie resistente.",
    ),
    (
        "pantallas",
        "Pantallas",
        'Monitor compacto 24"',
        16900,
        7,
        3200,
        "monitor.jpg",
        "El formato justo para espacios pequeños. Conexión sencilla y una imagen nítida.",
    ),
    (
        "accesorios",
        "Accesorios",
        "Reloj minimal",
        9900,
        5,
        72,
        "watch.jpg",
        "Detalles medidos y una estética atemporal. Diseñado para durar más de una temporada.",
    ),
    ("perifericos", "Periféricos", "Ratón de precisión", 7900, 11, 110, "mouse.jpg", "Desplazamiento suave y agarre cómodo para sesiones largas de trabajo."),
]


def seed(db):
    if db.scalar(select(Product.id).limit(1)):
        return
    categories = {}
    for slug, name, *_ in ITEMS:
        if slug not in categories:
            category = Category(slug=slug, name=name)
            db.add(category)
            db.flush()
            categories[slug] = category
    for slug, _, name, price, stock, weight, image, description in ITEMS:
        db.add(
            Product(
                name=name,
                description=description,
                price_cents=price,
                stock=stock,
                weight_grams=weight,
                image_url="/images/" + image,
                category_id=categories[slug].id,
            )
        )
    db.commit()
