import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PriceChart } from "./PriceChart";
import { money } from "./api";
describe("Histórico de precios", () => {
  it("distingue un historial vacío", () => {
    render(<PriceChart rows={[]} />);
    expect(screen.getByText(/todavía no ha cambiado/)).toBeInTheDocument();
  });
  it("representa el precio inicial y el actual", () => {
    render(
      <PriceChart
        rows={[
          {
            id: 1,
            previous_price_cents: 10000,
            price_cents: 9000,
            changed_at: "2026-10-19T12:00:00",
          },
        ]}
      />,
    );
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      `Evolución del precio: de ${money(10000)} a ${money(9000)}`,
    );
  });
  it("formatea céntimos sin multiplicar el precio", () => {
    expect(money(89900)).toMatch(/899/);
    expect(money(89900)).not.toMatch(/89.900/);
  });
});
