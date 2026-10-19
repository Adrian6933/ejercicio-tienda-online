import { useCallback, useEffect, useRef, useState } from "react";
import type { Cart, Category, Product, User } from "./types";
import { ApiError, image, money, post, request } from "./api";
import { useProducts } from "./hooks";
import { ProductDialog } from "./ProductDialog";
import { Account } from "./Account";
import { Checkout } from "./Checkout";
import "./style.css";
const empty: Cart = { items: [], total_cents: 0 };
function Bag() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      aria-hidden="true"
    >
      <path d="M5 8h14l1 13H4L5 8Z" />
      <path d="M8 9V6a4 4 0 0 1 8 0v3" />
    </svg>
  );
}
export default function App() {
  const [view, setView] = useState<"catalog" | "cart" | "account">("catalog"),
    [user, setUser] = useState<User | null>(null),
    [categories, setCategories] = useState<Category[]>([]),
    [category, setCategory] = useState(""),
    [search, setSearch] = useState(""),
    [draft, setDraft] = useState(""),
    [selected, setSelected] = useState<Product | null>(null),
    [cart, setCart] = useState<Cart>(empty),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [mode, setMode] = useState("demo");
  const token = useRef(localStorage.getItem("taller_cart") || ""),
    sentinel = useRef<HTMLDivElement>(null);
  const products = useProducts(category, search);
  const close = useCallback(() => setSelected(null), []);
  useEffect(() => {
    void request<User>("/me")
      .then(setUser)
      .catch(() => {});
    void request<Category[]>("/categories")
      .then(setCategories)
      .catch((e) => setError(e.message));
    void request<{ payment_mode: string }>("/health")
      .then((r) => setMode(r.payment_mode))
      .catch(() => {});
    if (token.current)
      void request<Cart>("/carts/" + token.current)
        .then(setCart)
        .catch(() => {
          token.current = "";
          localStorage.removeItem("taller_cart");
        });
  }, []);
  useEffect(() => {
    const timer = setTimeout(() => setSearch(draft), 250);
    return () => clearTimeout(timer);
  }, [draft]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 3500);
    return () => clearTimeout(timer);
  }, [notice]);
  useEffect(() => {
    if (!sentinel.current || !products.hasMore || products.loading) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) void products.loadMore();
      },
      { rootMargin: "160px" },
    );
    observer.observe(sentinel.current);
    return () => observer.disconnect();
  }, [products.hasMore, products.loading, products.items.length]);
  const add = async (product: Product) => {
    setBusy(true);
    setError("");
    try {
      if (!token.current) {
        token.current = (
          await request<{ token: string }>("/carts", post())
        ).token;
        localStorage.setItem("taller_cart", token.current);
      }
      const current =
        cart.items.find((i) => i.product.id === product.id)?.quantity || 0;
      setCart(
        await request<Cart>(`/carts/${token.current}/items/${product.id}`, {
          method: "PUT",
          body: JSON.stringify({ quantity: current + 1 }),
        }),
      );
      setNotice("Añadido al carrito");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const quantity = async (id: number, value: number) => {
    setBusy(true);
    setError("");
    try {
      setCart(
        await request<Cart>(`/carts/${token.current}/items/${id}`, {
          method: "PUT",
          body: JSON.stringify({ quantity: value }),
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const buy = async () => {
    if (!user) {
      setView("account");
      setNotice("Inicia sesión y guarda tu dirección de envío");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const order = await request<{ id: number }>(
        "/orders",
        post({ cart_token: token.current }),
      );
      token.current = "";
      localStorage.removeItem("taller_cart");
      setCart(empty);
      const payment = await request<{ url: string }>(
        `/orders/${order.id}/checkout`,
        post(),
      );
      window.location.assign(payment.url);
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.status === 401) setView("account");
    } finally {
      setBusy(false);
    }
  };
  const count = cart.items.reduce((sum, i) => sum + i.quantity, 0);
  const isCheckout = window.location.pathname.startsWith("/checkout/");
  return (
    <>
      <div className="topline">
        Una selección pequeña. Un espacio para grandes ideas.
        <span>
          {mode === "demo"
            ? "Tienda de práctica · pagos simulados"
            : "Stripe en modo de prueba"}
        </span>
      </div>
      <header className="header">
        <button
          className="brand"
          aria-label="Taller, ir al catálogo"
          onClick={() =>
            isCheckout ? window.location.assign("/") : setView("catalog")
          }
        >
          <span className="brand-mark">t</span>taller
          <span className="brand-period">.</span>
        </button>
        <nav aria-label="Navegación principal">
          <button
            className={view === "catalog" ? "active" : ""}
            onClick={() =>
              isCheckout ? window.location.assign("/") : setView("catalog")
            }
          >
            La selección
          </button>
          <button
            className={view === "account" ? "active" : ""}
            onClick={() =>
              isCheckout ? window.location.assign("/") : setView("account")
            }
          >
            {user ? "Mi cuenta" : "Entrar"}
          </button>
        </nav>
        <button
          className="bag"
          onClick={() => setView("cart")}
          aria-label={`Carrito, ${count} artículos`}
        >
          <Bag />
          <span>Carrito</span>
          <b>{count}</b>
        </button>
      </header>
      {error && (
        <div className="global-error" role="alert">
          {error}
          <button aria-label="Cerrar aviso" onClick={() => setError("")}>
            ×
          </button>
        </div>
      )}
      {isCheckout ? (
        <Checkout onBack={() => window.location.assign("/")} />
      ) : view === "account" ? (
        <Account user={user} onUser={setUser} onMessage={setNotice} />
      ) : view === "cart" ? (
        <main className="page">
          <span className="eyebrow">Tu selección</span>
          <h1>Buenas ideas, en tu carrito.</h1>
          {!cart.items.length ? (
            <div className="empty">
              <Bag />
              <h2>Aún hay espacio para algo bueno.</h2>
              <p className="muted">
                Explora la selección y encuentra tu próxima herramienta.
              </p>
              <button className="primary" onClick={() => setView("catalog")}>
                Volver al catálogo ↗
              </button>
            </div>
          ) : (
            <div className="cart-layout">
              <div>
                {cart.items.map(({ product, quantity: q }) => (
                  <article className="cart-item" key={product.id}>
                    <img src={image(product.image_url)} alt={product.name} />
                    <div>
                      <small className="eyebrow">{product.category.name}</small>
                      <h2>{product.name}</h2>
                      <p>{money(product.price_cents)}</p>
                      <div className="quantity">
                        <button
                          aria-label={`Quitar una unidad de ${product.name}`}
                          disabled={busy}
                          onClick={() => void quantity(product.id, q - 1)}
                        >
                          −
                        </button>
                        <span>{q}</span>
                        <button
                          aria-label={`Añadir una unidad de ${product.name}`}
                          disabled={busy || q >= product.stock}
                          onClick={() => void quantity(product.id, q + 1)}
                        >
                          +
                        </button>
                      </div>
                    </div>
                    <strong>{money(product.price_cents * q)}</strong>
                  </article>
                ))}
              </div>
              <aside className="summary">
                <h2>Un paso más.</h2>
                <div>
                  <span>Artículos ({count})</span>
                  <strong>{money(cart.total_cents)}</strong>
                </div>
                <div>
                  <span>Envío de la práctica</span>
                  <span>Incluido</span>
                </div>
                <div className="total">
                  <span>Total</span>
                  <strong>{money(cart.total_cents)}</strong>
                </div>
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => void buy()}
                >
                  {busy ? "Preparando…" : "Continuar con el pedido"}{" "}
                  <span>↗</span>
                </button>
                <p className="muted small">
                  Necesitarás una cuenta y una dirección de envío.{" "}
                  {mode === "demo"
                    ? "El pago se completa en el simulador local."
                    : "El pago se realiza en el entorno de pruebas de Stripe."}
                </p>
              </aside>
            </div>
          )}
        </main>
      ) : (
        <main>
          <section className="hero">
            <div>
              <span className="eyebrow">
                <span className="orange-dot" /> Objetos con propósito /
                Colección 01
              </span>
              <h1>
                El espacio para
                <br />
                tu próxima <em>idea.</em>
              </h1>
              <p>
                Herramientas bien elegidas para trabajar,
                <br />
                crear y hacer que las cosas pasen.
              </p>
              <a href="#catalogo" className="hero-link">
                Explorar la selección <span>↘</span>
              </a>
              <div className="hero-note">
                <span>01—12</span> Menos ruido. Más criterio.
              </div>
            </div>
            <div className="hero-visual">
              <span className="vertical-label">DISEÑADO PARA TU DÍA A DÍA</span>
              <img
                src={image("/images/laptop.jpg")}
                alt="Un portátil en un espacio de trabajo"
              />
              <div className="hero-caption">
                <span>
                  Las buenas ideas necesitan
                  <br />
                  buenas herramientas.
                </span>
                <span className="hero-arrow">↗</span>
              </div>
            </div>
          </section>
          <section className="catalog page" id="catalogo">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Elegidos uno a uno</span>
                <h2>Encuentra tu herramienta.</h2>
              </div>
              <label className="search">
                <span className="sr-only">Buscar productos</span>
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  aria-hidden="true"
                >
                  <circle cx="10" cy="10" r="6" />
                  <path d="m15 15 5 5" />
                </svg>
                <input
                  value={draft}
                  placeholder="Buscar en la selección"
                  onChange={(e) => setDraft(e.target.value)}
                />
              </label>
            </div>
            <div className="filters" aria-label="Filtrar por categoría">
              <button
                className={!category ? "selected" : ""}
                onClick={() => setCategory("")}
              >
                Toda la selección
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  className={category === c.slug ? "selected" : ""}
                  onClick={() => setCategory(c.slug)}
                >
                  {c.name}
                </button>
              ))}
            </div>
            {products.error ? (
              <div className="error" role="alert">
                {products.error}{" "}
                <button onClick={() => void products.retry()}>
                  Reintentar
                </button>
              </div>
            ) : null}
            <div className="product-grid">
              {products.items.map((p, i) => (
                <article className="product-card" key={p.id}>
                  <button
                    className="product-photo"
                    aria-label={`Ver ${p.name}`}
                    onClick={() => setSelected(p)}
                  >
                    <img
                      src={image(p.image_url)}
                      alt={p.name}
                      loading={i < 3 ? "eager" : "lazy"}
                    />
                    {!p.stock && (
                      <span className="soldout">Sin existencias</span>
                    )}
                    <span className="photo-arrow">↗</span>
                  </button>
                  <div className="product-meta">
                    <span className="eyebrow">{p.category.name}</span>
                    <h3>
                      <button onClick={() => setSelected(p)}>{p.name}</button>
                    </h3>
                    <div className="product-bottom">
                      <span>{money(p.price_cents)}</span>
                      <button
                        className="add-button"
                        disabled={!p.stock || busy}
                        aria-label={`Añadir ${p.name} al carrito`}
                        onClick={() => void add(p)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
            {!products.loading && !products.items.length && !products.error && (
              <div className="empty">
                <h3>No hemos encontrado productos.</h3>
                <p>Prueba con otra búsqueda o categoría.</p>
              </div>
            )}
            {products.loading && (
              <p className="loading" role="status">
                Cargando la selección…
              </p>
            )}
            <div ref={sentinel} />
            {products.hasMore && !products.loading && !products.error && (
              <button
                className="secondary more"
                onClick={() => void products.loadMore()}
              >
                Ver más productos ↓
              </button>
            )}
            <div className="catalog-end">
              <span>Elegir menos.</span>
              <span>Elegir mejor.</span>
              <span>Hacer más.</span>
            </div>
          </section>
        </main>
      )}
      <footer>
        <div className="brand">
          taller<span className="brand-period">.</span>
        </div>
        <p>
          Tecnología con criterio.
          <br />
          <span>Proyecto de Product Engineering · 2026</span>
        </p>
        <a
          href={
            import.meta.env.VITE_API_URL
              ? import.meta.env.VITE_API_URL + "/docs"
              : "http://localhost:8000/docs"
          }
          target="_blank"
          rel="noreferrer"
        >
          Documentación de la API ↗
        </a>
      </footer>
      {notice && (
        <div className="toast" role="status">
          ✓ {notice}
        </div>
      )}
      {selected && (
        <ProductDialog
          product={selected}
          user={user}
          onClose={close}
          onAdd={add}
          onChanged={() => {
            void products.retry();
          }}
        />
      )}
    </>
  );
}
