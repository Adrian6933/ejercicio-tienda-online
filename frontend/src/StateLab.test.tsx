import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { KeyCounter, LoadView, QuantityDemo } from "./StateLab";
afterEach(cleanup);
describe("Estado, refs y estados posibles", () => {
  it("acumula tres actualizaciones funcionales en el mismo evento", () => {
    render(<QuantityDemo />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button")).toHaveTextContent("Unidades: 3");
  });
  it("un ref acumula teclas sin actualizar el texto mostrado hasta pedirlo", () => {
    render(<KeyCounter />);
    fireEvent.keyDown(screen.getByLabelText("Prueba useRef"), { key: "a" });
    fireEvent.keyDown(screen.getByLabelText("Prueba useRef"), { key: "b" });
    expect(screen.getByRole("status")).toHaveTextContent("0");
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("status")).toHaveTextContent("2");
  });
  it("cada estado tiene una vista explícita", () => {
    const { rerender } = render(
      <LoadView state={{ status: "loading" }} render={() => "ok"} />,
    );
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    rerender(
      <LoadView
        state={{ status: "error", message: "Sin conexión" }}
        render={() => "ok"}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Sin conexión");
    rerender(
      <LoadView
        state={{ status: "ready", data: 3 }}
        render={(n) => `${n} productos`}
      />,
    );
    expect(screen.getByText("3 productos")).toBeInTheDocument();
  });
});
