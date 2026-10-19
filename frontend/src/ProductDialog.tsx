import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { image, money, post, request } from "./api";
import type { History, Product, User } from "./types";
import { PriceChart } from "./PriceChart";
export function ProductDialog({
  product,
  user,
  onClose,
  onAdd,
  onChanged,
}: {
  product: Product;
  user: User | null;
  onClose: () => void;
  onAdd: (p: Product) => Promise<void>;
  onChanged: () => void;
}) {
  const [rows, setRows] = useState<History[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [newPrice, setNewPrice] = useState(String(product.price_cents));
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const controller = new AbortController();
    request<History[]>(`/products/${product.id}/price-history`, {
      signal: controller.signal,
    })
      .then(setRows)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    void request(`/products/${product.id}/views`, post()).catch(() => {});
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") {
        const focus = ref.current?.querySelectorAll<HTMLElement>(
          "button,input,summary,a[href]",
        );
        if (!focus?.length) return;
        const first = focus[0],
          last = focus[focus.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => {
      controller.abort();
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, [product.id, onClose]);
  return createPortal(
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="product-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="product-title"
        ref={ref}
      >
        <button
          className="close icon-button"
          aria-label="Cerrar detalle"
          onClick={onClose}
        >
          ×
        </button>
        <div className="dialog-photo">
          <img src={image(product.image_url)} alt={product.name} />
        </div>
        <div className="dialog-content">
          <span className="eyebrow">{product.category.name}</span>
          <h2 id="product-title">{product.name}</h2>
          <p className="product-price">{money(product.price_cents)}</p>
          <p className="muted">{product.description}</p>
          <p className="stock">
            {product.stock > 0
              ? `${product.stock} unidades disponibles`
              : "Sin existencias"}{" "}
            ·{" "}
            {product.weight_grams
              ? `${product.weight_grams} g`
              : "Peso sin definir"}
          </p>
          <button
            className="primary"
            disabled={!product.stock || busy}
            onClick={async () => {
              setBusy(true);
              try {
                await onAdd(product);
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Añadiendo…" : "Añadir al carrito"} <span>↗</span>
          </button>
          <section className="history">
            <h3>El precio, con perspectiva</h3>
            <PriceChart rows={rows} />
          </section>
          {user?.is_admin && (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setBusy(true);
                try {
                  await request(`/products/${product.id}/price`, {
                    method: "PUT",
                    body: JSON.stringify({ price_cents: Number(newPrice) }),
                  });
                  setRows(
                    await request<History[]>(
                      `/products/${product.id}/price-history`,
                    ),
                  );
                  onChanged();
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              <label>
                Nuevo precio en céntimos
                <input
                  type="number"
                  min="1"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                />
              </label>
              <button disabled={busy} className="secondary">
                Guardar precio
              </button>
            </form>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
