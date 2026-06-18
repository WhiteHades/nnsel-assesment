import { expect, test } from "@playwright/test";

test("presentation loads and links to the implementation scope", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => {
    consoleErrors.push(error.message);
  });

  await page.goto("/");

  await expect(page).toHaveTitle(/NNSEL Fund Management/);
  await expect(page.getByRole("heading", { name: "NN Fund Management" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Repository" })).toHaveAttribute(
    "href",
    "https://github.com/WhiteHades/nnsel-assesment",
  );

  await page.getByRole("link", { name: "View scope" }).click();
  await expect(page.locator("#coverage")).toBeInViewport({ ratio: 0.2 });
  expect(consoleErrors).toEqual([]);
});
