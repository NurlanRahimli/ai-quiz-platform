import { expect, test } from "@playwright/test"

test("complete authentication flow", async ({ page }) => {
  const uniqueId = Date.now()
  const displayName = "Integration Test User"
  const email = `integration-${uniqueId}@example.com`
  const password = "Testing123!"

  // Register
  await page.goto("/register")

  await page.getByLabel("Display name").fill(displayName)
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password", { exact: true }).fill(password)
  await page.getByLabel("Confirm password").fill(password)

  await page.getByRole("button", { name: "Create account" }).click()

  await expect(
    page.getByText("Account created successfully. You can now log in."),
  ).toBeVisible()

  // Login
  await page.getByRole("link", { name: "Log in" }).click()

  await expect(page).toHaveURL(/\/login$/)
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible()

  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password", { exact: true }).fill(password)

  const loginRequestPromise = page.waitForRequest(
    (request) =>
      request.url().endsWith("/api/v1/auth/login") &&
      request.method() === "POST",
  )

  await page.getByRole("button", { name: "Log in" }).click()

  const loginRequest = await loginRequestPromise
  const loginResponse = await loginRequest.response()

  expect(loginResponse).not.toBeNull()
  expect(loginResponse!.status()).toBe(200)

  const loginBody = await loginResponse!.json()

  expect(loginBody.access_token).toBeTruthy()
  expect(loginBody.token_type).toBe("bearer")

  // React stores the JWT
  const storedToken = await page.evaluate(() =>
    localStorage.getItem("ai_quiz_access_token"),
  )

  expect(storedToken).toBe(loginBody.access_token)

  // Successful login redirects to the protected dashboard
  await expect(page).toHaveURL(/\/dashboard$/)

  await expect(
    page.getByRole("heading", {
      name: `Welcome back, ${displayName}.`,
    }),
  ).toBeVisible()

  // Refreshing restores the authenticated session
  await page.reload()

  await expect(page).toHaveURL(/\/dashboard$/)

  await expect(
    page.getByRole("heading", {
      name: `Welcome back, ${displayName}.`,
    }),
  ).toBeVisible()

  // Logout clears the session
  await page.getByRole("button", { name: "Logout" }).click()

  await expect(page).toHaveURL(/\/login$/)

  const tokenAfterLogout = await page.evaluate(() =>
    localStorage.getItem("ai_quiz_access_token"),
  )

  expect(tokenAfterLogout).toBeNull()

  // Protected dashboard is no longer accessible
  await page.goto("/dashboard")

  await expect(page).toHaveURL(/\/login$/)
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible()
})