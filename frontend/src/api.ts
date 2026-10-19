export const API = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/$/, "");
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(API + path, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: "No se pudo completar la petición" }));
    throw new ApiError(
      response.status,
      typeof body.detail === "string"
        ? body.detail
        : "Revisa los campos del formulario",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const money = (cents: number) =>
  new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" }).format(
    cents / 100,
  );
export const image = (url: string) => (url.startsWith("/") ? API + url : url);
export const post = (value?: unknown): RequestInit => ({
  method: "POST",
  ...(value === undefined ? {} : { body: JSON.stringify(value) }),
});
