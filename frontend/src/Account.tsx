import { useEffect, useState } from "react";
import { money, post, request } from "./api";
import type { Address, Order, User } from "./types";
const empty: Address = {
  recipient: "",
  street: "",
  city: "",
  postal_code: "",
  country: "ES",
};
const statusName: Record<string, string> = {
  pending_payment: "Pendiente de pago",
  paid: "Pagado",
  expired: "Reserva caducada",
  partially_refunded: "Reembolso parcial",
  refunded: "Reembolsado",
};
export function Account({
  user,
  onUser,
  onMessage,
}: {
  user: User | null;
  onUser: (u: User | null) => void;
  onMessage: (s: string) => void;
}) {
  const [register, setRegister] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [orders, setOrders] = useState<Order[]>([]),
    [shipping, setShipping] = useState<Address>(empty),
    [billing, setBilling] = useState<Address>(empty),
    [loaded, setLoaded] = useState(false);
  useEffect(() => {
    if (!user) return;
    let active = true;
    setLoaded(false);
    Promise.all([
      request<Address | null>("/me/addresses/shipping"),
      request<Address | null>("/me/addresses/billing"),
      request<Order[]>("/me/orders"),
    ])
      .then(([s, b, o]) => {
        if (active) {
          setShipping(s || empty);
          setBilling(b || empty);
          setOrders(o);
          setLoaded(true);
        }
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [user]);
  if (!user)
    return (
      <main className="page narrow">
        <span className="eyebrow">Tu espacio</span>
        <h1>
          {register ? "Empecemos algo bueno." : "Qué bien verte de nuevo."}
        </h1>
        <p className="muted">Guarda tus direcciones y sigue tus pedidos.</p>
        <form
          className="form-card"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const form = new FormData(e.currentTarget),
              email = String(form.get("email")),
              password = String(form.get("password"));
            try {
              if (register)
                await request(
                  "/auth/register",
                  post({ email, password, name: form.get("name") }),
                );
              onUser(
                await request<User>("/auth/login", post({ email, password })),
              );
              onMessage("Ya estás dentro");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {register && (
            <label>
              Nombre
              <input name="name" autoComplete="name" minLength={2} required />
            </label>
          )}
          <label>
            Email
            <input type="email" name="email" autoComplete="email" required />
          </label>
          <label>
            Contraseña
            <input
              name="password"
              type="password"
              minLength={register ? 10 : 1}
              autoComplete={register ? "new-password" : "current-password"}
              required
            />
          </label>
          {register && (
            <small className="muted">Usa al menos 10 caracteres.</small>
          )}
          <button className="primary" disabled={busy}>
            {busy
              ? "Un momento…"
              : register
                ? "Crear mi cuenta"
                : "Iniciar sesión"}{" "}
            <span>↗</span>
          </button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <button
            type="button"
            className="text-button"
            onClick={() => {
              setRegister(!register);
              setError("");
            }}
          >
            {register ? "Ya tengo una cuenta" : "Crear una cuenta"}
          </button>
        </form>
      </main>
    );
  return (
    <main className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Mi cuenta</span>
          <h1>Hola, {user.name.split(" ")[0]}.</h1>
        </div>
        <button
          className="secondary"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await request("/auth/logout", post());
              onUser(null);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          Cerrar sesión
        </button>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!loaded ? (
        <p>Cargando tu cuenta…</p>
      ) : (
        <>
          <div className="address-grid">
            {(["shipping", "billing"] as const).map((kind) => {
              const address = kind === "shipping" ? shipping : billing,
                setAddress = kind === "shipping" ? setShipping : setBilling;
              return (
                <form
                  key={kind}
                  className="form-card"
                  onSubmit={async (e) => {
                    e.preventDefault();
                    setBusy(true);
                    setError("");
                    try {
                      const { recipient, street, city, postal_code, country } =
                        address;
                      await request("/me/addresses/" + kind, {
                        method: "PUT",
                        body: JSON.stringify({
                          recipient,
                          street,
                          city,
                          postal_code,
                          country,
                        }),
                      });
                      onMessage("Dirección guardada");
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  <h2>
                    {kind === "shipping"
                      ? "Dirección de envío"
                      : "Dirección de facturación"}
                  </h2>
                  {kind === "billing" && (
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => setBilling({ ...shipping })}
                    >
                      Copiar de envío ↗
                    </button>
                  )}
                  {(
                    [
                      ["recipient", "Destinatario"],
                      ["street", "Calle y número"],
                      ["city", "Ciudad"],
                      ["postal_code", "Código postal"],
                      ["country", "País (ES, PT…)"],
                    ] as const
                  ).map(([field, label]) => (
                    <label key={field}>
                      {label}
                      <input
                        aria-label={`${label} ${kind}`}
                        required
                        value={address[field]}
                        minLength={2}
                        maxLength={field === "country" ? 2 : 200}
                        onChange={(e) =>
                          setAddress({
                            ...address,
                            [field]:
                              field === "country"
                                ? e.target.value.toUpperCase()
                                : e.target.value,
                          })
                        }
                      />
                    </label>
                  ))}
                  <button className="secondary" disabled={busy}>
                    Guardar {kind === "shipping" ? "envío" : "facturación"}
                  </button>
                </form>
              );
            })}
          </div>
          <section className="orders">
            <h2>Tus pedidos</h2>
            {!orders.length ? (
              <p className="muted">
                Tu próxima idea empieza en el catálogo. Aún no hay pedidos.
              </p>
            ) : (
              orders.map((order) => (
                <article className="order" key={order.id}>
                  <div>
                    <strong>Pedido #{order.id}</strong>
                    <p className="muted">
                      {order.items
                        .map((i) => `${i.quantity} × ${i.name}`)
                        .join(" · ")}
                    </p>
                    <span
                      className={
                        "badge " + (order.status === "paid" ? "green" : "")
                      }
                    >
                      {statusName[order.status] || order.status}
                    </span>
                  </div>
                  <div>
                    <strong>{money(order.total_cents)}</strong>
                    {order.refunded_cents > 0 && (
                      <small>Reembolsado: {money(order.refunded_cents)}</small>
                    )}
                    {order.status === "pending_payment" && (
                      <button
                        className="secondary"
                        disabled={busy}
                        onClick={async () => {
                          setBusy(true);
                          try {
                            const result = await request<{ url: string }>(
                              `/orders/${order.id}/checkout`,
                              post(),
                            );
                            window.location.assign(result.url);
                          } catch (e) {
                            setError((e as Error).message);
                            setBusy(false);
                          }
                        }}
                      >
                        Continuar pago ↗
                      </button>
                    )}
                  </div>
                </article>
              ))
            )}
          </section>
        </>
      )}
    </main>
  );
}
