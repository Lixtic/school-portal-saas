const { chromium } = require('playwright');

async function run() {
    const baseUrl = (process.env.BASE_URL || 'http://127.0.0.1:8765').replace(/\/$/, '');
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    try {
        await page.goto(`${baseUrl}/login/`, { waitUntil: 'networkidle' });

        const hasLoaderHooks = await page.evaluate(() => {
            return Boolean(document.getElementById('pageLoader')) && Boolean(document.getElementById('globalLoader'));
        });
        if (!hasLoaderHooks) {
            throw new Error('Missing global loader hooks on /login/.');
        }

        // Validate explicit loader control API is wired.
        await page.evaluate(() => window.showLoader('Smoke test...'));
        await page.waitForSelector('#globalLoader.active', { timeout: 5000 });

        await page.evaluate(() => window.hideLoader());
        await page.waitForTimeout(900);

        const postHideState = await page.evaluate(() => {
            const bar = document.getElementById('pageLoader');
            const overlay = document.getElementById('globalLoader');
            return {
                barLoading: Boolean(bar && bar.classList.contains('loading')),
                overlayActive: Boolean(overlay && overlay.classList.contains('active')),
            };
        });
        if (postHideState.barLoading || postHideState.overlayActive) {
            throw new Error('Loader stayed active after hideLoader() call.');
        }

        // Validate navigation does not leave loader stuck.
        const resetLink = page.locator('a[href*="password_reset"]').first();
        if (await resetLink.count()) {
            await Promise.all([
                page.waitForURL(/password_reset\//, { timeout: 10000 }),
                resetLink.click(),
            ]);
        } else {
            await page.goto(`${baseUrl}/password_reset/`, { waitUntil: 'networkidle' });
        }

        const postNavigationState = await page.evaluate(() => {
            const bar = document.getElementById('pageLoader');
            const overlay = document.getElementById('globalLoader');
            return {
                barLoading: Boolean(bar && bar.classList.contains('loading')),
                overlayActive: Boolean(overlay && overlay.classList.contains('active')),
            };
        });
        if (postNavigationState.barLoading || postNavigationState.overlayActive) {
            throw new Error('Loader stuck after navigation.');
        }

        console.log('Loader smoke test passed.');
    } finally {
        await browser.close();
    }
}

run().catch((err) => {
    console.error(err);
    process.exit(1);
});
