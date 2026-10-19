import { useRef, useState } from "react";
import type { ReactNode } from "react";
import type { LoadState } from "./types";

// Ejemplos de estado, probados por separado del flujo de compra.
export function QuantityDemo() {
  const [units, setUnits] = useState(0);
  return (
    <button
      onClick={() => {
        setUnits((value) => value + 1);
        setUnits((value) => value + 1);
        setUnits((value) => value + 1);
      }}
    >
      Unidades: {units}
    </button>
  );
}

export function KeyCounter() {
  const keys = useRef(0);
  const [shown, setShown] = useState(0);
  return (
    <div>
      <input
        aria-label="Prueba useRef"
        onKeyDown={() => {
          keys.current += 1;
        }}
      />
      <button onClick={() => setShown(keys.current)}>Mostrar contador</button>
      <output>{shown}</output>
    </div>
  );
}

export function LoadView<T>({
  state,
  render,
}: {
  state: LoadState<T>;
  render: (data: T) => ReactNode;
}) {
  switch (state.status) {
    case "loading":
      return <p>Cargando…</p>;
    case "error":
      return <p role="alert">{state.message}</p>;
    case "ready":
      return <>{render(state.data)}</>;
  }
}
