import { useEffect, useState } from "react";
import { money, post, request } from "./api";
import type { Order } from "./types";
export function Checkout({ onBack }: { onBack: () => void }) {
  const path = window.location.pathname,
    params = new URLSearchParams(window.location.search),
    orderId = params.get("order");
  const [order, setOrder] = useState<Order | null>(null),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (orderId)
      request<Order>(`/orders/${orderId}`)
        .then(setOrder)
        .catch((e) => setError(e.message));
    else if (params.get("session_id"))
      request<Order[]>("/me/orders")
        .then((values) =>
          setOrder(
            values.find(
              (o) => o.checkout_session_id === params.get("session_id"),
            ) || null,
          ),
        )
        .catch((e) => setError(e.message));
  }, [orderId]);
  const result = async (outcome: string) => {
    setBusy(true);
    setError("");
    try {
      const value = await request<Order>(
        `/orders/${orderId}/demo-result`,
        post({ outcome }),
      );
      setOrder(value);
      setMessage(
        outcome === "paid"
          ? "Pago de demostración completado."
          : outcome === "expired"
            ? "Reserva cancelada y stock devuelto."
            : outcome === "declined"
              ? "Pago rechazado. El pedido sigue pendiente."
              : "Autenticación adicional requerida. Puedes completarla con el botón de éxito.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="page narrow">
      <span className="eyebrow">
        {path.endsWith("/demo") ? "Simulador local · sin cobros" : "Tu pedido"}
      </span>
      <h1>
        {order?.status === "paid"
          ? "Todo listo. Gracias."
          : path.endsWith("/cancel")
            ? "Puedes seguir cuando quieras."
            : path.endsWith("/success")
              ? "Comprobando tu pago."
              : "Probemos el recorrido."}
      </h1>
      {order && (
        <div className="form-card">
          <h2>Pedido #{order.id}</h2>
          <p>{order.items.map((i) => i.name).join(" · ")}</p>
          <strong className="product-price">{money(order.total_cents)}</strong>
          <p>Estado: {order.status}</p>
          {path.endsWith("/demo") && order.status === "pending_payment" && (
            <>
              <p className="muted">
                Esto es un simulador de la práctica. Stripe no interviene y no
                se introduce ninguna tarjeta.
              </p>
              <div className="demo-actions">
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => void result("paid")}
                >
                  Simular pago correcto
                </button>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => void result("declined")}
                >
                  Simular rechazo
                </button>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => void result("requires_action")}
                >
                  Simular 3DS
                </button>
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => void result("expired")}
                >
                  Cancelar y liberar stock
                </button>
              </div>
            </>
          )}
          {path.endsWith("/success") && order.status !== "paid" && (
            <p className="muted">
              Esperando la confirmación del proveedor. Llegar a esta página no
              marca el pedido como pagado. Actualiza tu cuenta en unos segundos.
            </p>
          )}
        </div>
      )}
      {message && <p role="status">{message}</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button className="secondary" onClick={onBack}>
        Volver al catálogo ←
      </button>
    </main>
  );
}
