export type Category = { id: number; name: string; slug: string };
export type Product = {
  id: number;
  name: string;
  description: string;
  price_cents: number;
  stock: number;
  weight_grams: number | null;
  image_url: string;
  category: Category;
};
export type User = {
  id: number;
  name: string;
  email: string;
  is_admin: boolean;
};
export type Cart = {
  items: { product: Product; quantity: number }[];
  total_cents: number;
};
export type Address = {
  id?: number;
  recipient: string;
  street: string;
  city: string;
  postal_code: string;
  country: string;
};
export type Order = {
  id: number;
  status: string;
  total_cents: number;
  refunded_cents: number;
  created_at: string;
  items: {
    product_id: number;
    name: string;
    price_cents: number;
    quantity: number;
  }[];
  checkout_session_id: string | null;
};
export type History = {
  id: number;
  previous_price_cents: number;
  price_cents: number;
  changed_at: string;
};
export type LoadState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };
