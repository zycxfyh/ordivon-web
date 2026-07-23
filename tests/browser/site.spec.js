import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";

const routes = [
  "/",
  "/work/",
  "/work/ordivon-runtime/",
  "/work/finharness/",
  "/work/ordivon-web/",
  "/notes/",
  "/notes/ordivon-runtime-release/",
  "/notes/why-ordivon/",
  "/now/",
  "/about/",
  "/contact/",
];

const screenshotRoutes = new Set([
  "/",
  "/work/",
  "/work/ordivon-runtime/",
  "/notes/",
  "/about/",
]);

function routeSlug(route) {
  return route === "/" ? "home" : route.replace(/^\//, "").replace(/\/$/, "").replaceAll("/", "-");
}

for (const route of routes) {
  test(`${route} remains usable`, async ({ page }, testInfo) => {
    const browserErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("pageerror", (error) => browserErrors.push(error.message));

    const response = await page.goto(route, { waitUntil: "networkidle" });
    expect(response?.status()).toBe(200);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("Ordinary Prosperity");

    const dimensions = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);

    const viewport = page.viewportSize();
    if (!viewport) throw new Error("viewport is unavailable");

    if (viewport.width <= 840) {
      await expect(page.locator(".desktop-navigation")).toBeHidden();
      const summary = page.locator(".mobile-navigation summary");
      await summary.focus();
      await page.keyboard.press("Enter");
      await expect(page.locator(".mobile-navigation")).toHaveAttribute("open", "");
      const targetHeights = await page.locator(".mobile-navigation nav a").evaluateAll((nodes) =>
        nodes.map((node) => node.getBoundingClientRect().height),
      );
      expect(Math.min(...targetHeights)).toBeGreaterThanOrEqual(44);
    } else {
      await expect(page.locator(".desktop-navigation")).toBeVisible();
      await expect(page.locator(".mobile-navigation")).toBeHidden();
    }

    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    const serious = accessibility.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact ?? ""),
    );
    expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
    expect(browserErrors, browserErrors.join("\n")).toEqual([]);

    if (screenshotRoutes.has(route)) {
      await fs.mkdir("artifacts/screenshots", { recursive: true });
      await page.screenshot({
        path: `artifacts/screenshots/${testInfo.project.name}-${routeSlug(route)}.png`,
        fullPage: true,
      });
    }
  });
}

test("keyboard focus begins with the skip link", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
});
