import { test, expect } from "@playwright/test";

test("catálogo, búsqueda, detalle y navegación con teclado", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /El espacio para/ }),
  ).toBeVisible();
  await expect(page.locator(".product-card")).toHaveCount(6);
  await page.getByRole("button", { name: "Audio", exact: true }).click();
  await expect(page.locator(".product-card")).toHaveCount(2);
  await page.getByRole("button", { name: "Toda la selección" }).click();
  await page.getByPlaceholder("Buscar en la selección").fill("Portátil");
  await expect(page.locator(".product-card")).toHaveCount(2);
  await page
    .getByRole("button", { name: 'Ver Portátil de aluminio 14"', exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(
    page.getByText("Este producto todavía no ha cambiado de precio."),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
});

test("recorrido completo: cuenta, dirección, carrito, pedido y pago demo", async ({
  page,
}) => {
  const email = "e2e-" + Date.now() + "@example.test";
  await page.goto("/");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await page
    .getByRole("button", { name: "Crear una cuenta", exact: true })
    .click();
  await page.getByLabel("Nombre", { exact: true }).fill("Estudiante E2E");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Prueba-larga-2026");
  await page.getByRole("button", { name: /^Crear mi cuenta/ }).click();
  await expect(
    page.getByRole("heading", { name: "Hola, Estudiante." }),
  ).toBeVisible();
  for (const [field, value] of [
    ["Destinatario", "Estudiante"],
    ["Calle y número", "Calle ficticia 1"],
    ["Ciudad", "Madrid"],
    ["Código postal", "28000"],
    ["País (ES, PT…)", "ES"],
  ])
    await page.getByLabel(field + " shipping", { exact: true }).fill(value);
  await page
    .getByRole("button", { name: "Guardar envío", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Dirección guardada");
  await page.getByRole("button", { name: "La selección", exact: true }).click();
  await page
    .getByRole("button", {
      name: 'Añadir Portátil de aluminio 14" al carrito',
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Carrito, 1 artículos", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Buenas ideas, en tu carrito." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Continuar con el pedido" }).click();
  await expect(page).toHaveURL(/checkout\/demo\?order=/);
  await expect(page.getByText("Simulador local · sin cobros")).toBeVisible();
  await page.getByRole("button", { name: "Simular rechazo" }).click();
  await expect(
    page.getByText("Pago rechazado. El pedido sigue pendiente."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Simular pago correcto" }).click();
  await expect(
    page.getByRole("heading", { name: "Todo listo. Gracias." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Volver al catálogo ←" }).click();
  await page.getByRole("button", { name: "Mi cuenta", exact: true }).click();
  await expect(page.getByText("Pagado", { exact: true })).toBeVisible();
});

test("móvil: sin desbordamiento y catálogo accesible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.locator(".product-card").first()).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("button", { name: 'Ver Portátil de aluminio 14"', exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Cerrar detalle" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
