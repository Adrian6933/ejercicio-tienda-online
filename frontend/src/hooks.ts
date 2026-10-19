import { useCallback, useEffect, useRef, useState } from "react";
import { request } from "./api";
import type { Product } from "./types";

export function useProducts(category: string, search: string) {
  const [items, setItems] = useState<Product[]>([]),
    [cursor, setCursor] = useState<number | null>(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const sequence = useRef(0),
    busy = useRef(false),
    abort = useRef<AbortController | null>(null);
  const load = useCallback(
    async (next: number, replace = false) => {
      if (busy.current && !replace) return;
      if (replace) {
        abort.current?.abort();
        sequence.current++;
      }
      const seq = sequence.current,
        controller = new AbortController();
      abort.current = controller;
      busy.current = true;
      setLoading(true);
      setError("");
      const params = new URLSearchParams({
        limit: "6",
        cursor: String(next),
        q: search,
      });
      if (category) params.set("category", category);
      try {
        const page = await request<{
          items: Product[];
          next_cursor: number | null;
        }>("/products?" + params, { signal: controller.signal });
        if (seq === sequence.current) {
          setItems((old) =>
            replace
              ? page.items
              : [
                  ...old,
                  ...page.items.filter((p) => !old.some((o) => o.id === p.id)),
                ],
          );
          setCursor(page.next_cursor);
        }
      } catch (e) {
        if (
          seq === sequence.current &&
          !(e instanceof DOMException && e.name === "AbortError")
        )
          setError(e instanceof Error ? e.message : "Error al cargar");
      } finally {
        if (seq === sequence.current) {
          busy.current = false;
          setLoading(false);
        }
      }
    },
    [category, search],
  );
  useEffect(() => {
    setItems([]);
    setCursor(0);
    void load(0, true);
    return () => {
      abort.current?.abort();
      sequence.current++;
    };
  }, [load]);
  return {
    items,
    loading,
    error,
    hasMore: cursor !== null,
    loadMore: () => (cursor !== null ? load(cursor) : Promise.resolve()),
    retry: () => load(0, true),
  };
}
