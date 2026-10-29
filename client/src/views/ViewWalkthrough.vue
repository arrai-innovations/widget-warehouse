<script setup>
import Button from "@vueda/controls/button/Button.vue";
import { storeUser } from "@vueda/stores/storeUser.js";
import { useTitle } from "@vueuse/core";
import { RouterLink, useRoute } from "vue-router";

import { DEMO_ACCOUNTS, DEMO_PASSWORD } from "@/demoAccounts.js";

const route = useRoute();
const userStore = storeUser();
useTitle("Demo walkthrough | Widget Warehouse");

const sections = [
    { id: "accounts", title: "Choose an account" },
    { id: "shortage", title: "1. Find stock to replenish" },
    { id: "draft", title: "2. Prepare an order" },
    { id: "approve", title: "3. Approve the order" },
    { id: "warnings", title: "Try a stock-count warning" },
    { id: "explore", title: "Explore more of the demo" },
];
</script>

<template>
    <main class="mx-auto max-w-6xl px-5 pt-32 pb-16 sm:px-8">
        <header class="max-w-3xl">
            <p class="mb-3 text-sm font-medium tracking-widest text-muted-foreground uppercase">Widget Warehouse</p>
            <h1 class="text-3xl leading-tight font-bold tracking-tight sm:text-4xl">Demo walkthrough</h1>
            <p class="mt-5 text-lg leading-relaxed">
                Find stock to replenish, prepare a purchase order, and approve it with a different account. This
                exercise shows VUEDA's forms, permissions, workflows, and a custom replenishment action working
                together.
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
                <Button as-child tone="primary">
                    <RouterLink :to="{ name: userStore.loggedIn ? 'dashboard' : 'sign-in' }">
                        {{ userStore.loggedIn ? "Return to dashboard" : "Choose a demo account" }}
                    </RouterLink>
                </Button>
                <Button as-child emphasis="outline">
                    <RouterLink :to="route.fullPath" target="_blank" rel="noopener">Open guide in a new tab</RouterLink>
                </Button>
            </div>
            <p class="mt-3 text-sm text-muted-foreground">
                Keep the guide in a separate tab while you use the application. There is no progress tracker or
                automatic account switching.
            </p>
        </header>

        <div class="mt-10 grid items-start gap-10 lg:grid-cols-[14rem_minmax(0,1fr)] lg:gap-14">
            <nav aria-label="Walkthrough sections" class="border-y-hairline py-4 lg:sticky lg:top-6">
                <p class="mb-3 text-sm font-semibold">In this guide</p>
                <ul class="space-y-3 text-sm">
                    <li v-for="section in sections" :key="section.id">
                        <RouterLink
                            :to="{ name: 'walkthrough', hash: `#${section.id}` }"
                            class="underline underline-offset-4"
                        >
                            {{ section.title }}
                        </RouterLink>
                    </li>
                </ul>
            </nav>

            <article class="guide min-w-0 max-w-3xl text-base leading-relaxed">
                <aside class="border-hairline bg-muted/30 p-5" aria-label="Before you begin">
                    <h2>Before you begin</h2>
                    <p>
                        The hosted demo is shared. Other visitors can change the same records, and operator resets
                        discard demo changes. Use sample data only. The steps below use current stock and order
                        quantities, so they do not require a fresh reset.
                    </p>
                    <p>
                        The exercise ends with approved incoming stock covering a shortage.
                        <strong>On-hand stock does not increase.</strong> Receiving an order only records a workflow
                        state; stock posting and partial receipts are not implemented.
                    </p>
                </aside>

                <section id="accounts">
                    <h2>Choose an account</h2>
                    <p>
                        On the <RouterLink :to="{ name: 'sign-in' }">sign-in page</RouterLink>, select an account to
                        fill the form, then sign in. Every account uses the password <code>{{ DEMO_PASSWORD }}</code
                        >. Start this walkthrough as the <strong>Inventory supervisor</strong>.
                    </p>
                    <dl class="divide-y divide-border">
                        <div v-for="account in DEMO_ACCOUNTS" :key="account.email" class="py-4">
                            <dt class="font-semibold">{{ account.role }}</dt>
                            <dd class="mt-1 break-words font-mono text-sm text-muted-foreground">
                                {{ account.email }}
                            </dd>
                            <dd class="mt-2">{{ account.description }}</dd>
                        </div>
                    </dl>
                    <p>
                        To switch roles, choose <strong>Sign Out</strong> in the application's sidebar, then select
                        another account. Record your stock-item label and order reference so you can find them after
                        signing in again. Menus and available actions change with the account.
                    </p>
                </section>

                <section id="shortage">
                    <p class="role">Step 1 / Inventory supervisor</p>
                    <h2>Find stock to replenish</h2>
                    <ol>
                        <li>
                            Open <strong>Inventory Records</strong>. If any filters are already applied, choose
                            <strong>Clear filters</strong>.
                        </li>
                        <li>
                            Set <strong>Below reorder threshold</strong>, <strong>Product active</strong>,
                            <strong>Warehouse active</strong>, <strong>Supplier active</strong>, and
                            <strong>Supplier approved</strong> to <strong>Yes</strong>.
                        </li>
                        <li>
                            Select an item's checkbox and choose <strong>Replenish</strong>. Check its proposed
                            quantity. If existing orders already cover the shortage, try another item.
                        </li>
                        <li>
                            When an item has a positive proposed quantity, record its stock-item label. Do not create an
                            order yet. Continue to <strong>Step 2: Prepare an order</strong>.
                        </li>
                    </ol>
                    <h3>If no item needs another order</h3>
                    <ol>
                        <li>
                            Return to <strong>Inventory Records</strong> and remove the
                            <strong>Below reorder threshold</strong> filter. Keep the four eligibility filters set to
                            <strong>Yes</strong>.
                        </li>
                        <li>
                            Choose an item, select its checkbox, and open <strong>Replenish</strong>. Add
                            <strong>On hand</strong> and both quantities under <strong>Incoming / Pending</strong>.
                        </li>
                        <li>
                            Return to the list and choose <strong>Update</strong> for that item. Set
                            <strong>Reorder threshold</strong> to that total plus <strong>10</strong>, and
                            <strong>Max stock level</strong> to that total plus <strong>20</strong>. Leave
                            <strong>Quantity on hand</strong> unchanged and save.
                        </li>
                        <li>
                            Open <strong>Review shortages</strong> and search for the item's label. Keep that label for
                            Step 2.
                        </li>
                    </ol>
                    <p class="callout">
                        <strong>Example:</strong> with 5 on hand, 12 incoming, and 8 pending, the total is 25. Set the
                        threshold to <strong>35</strong> and the maximum to <strong>45</strong>. This creates a
                        purchasing requirement beyond what existing orders cover.
                    </p>
                </section>

                <section id="draft">
                    <p class="role">Step 2 / Inventory clerk</p>
                    <h2>Prepare an order</h2>
                    <ol>
                        <li>
                            Switch to <strong>Inventory clerk</strong>. Open <strong>Inventory Records</strong>, choose
                            <strong>Review shortages</strong>, and search for the stock-item label you saved. Select the
                            same item. The clerk can read its stock and targets but cannot update them.
                        </li>
                        <li>
                            Choose <strong>Replenish</strong>. Review the proposed quantity, which accounts for existing
                            pending orders and approved incoming stock. The page groups selected items by supplier and
                            destination warehouse. Select additional items to see multiple groups.
                        </li>
                        <li>
                            Keep the proposed quantity. You can change <strong>Unit price</strong>; enter a sample price
                            if none is stored. Choose <strong>Create 1 draft purchase order</strong> (the count changes
                            when selecting multiple groups). The order list opens filtered to your new batch. Note the
                            order's <strong>Reference</strong>; <strong>Show all orders</strong> removes the batch
                            filter.
                        </li>
                        <li>
                            Choose <strong>Update</strong> on the draft to explore its order lines. To try a delivery
                            warning, check the supplier's <strong>Typical lead days</strong> and set an
                            <strong>Expected arrival date</strong> earlier than that lead time after the
                            <strong>Order date</strong>. For a lead time greater than one day, use the next day. Save,
                            then cancel the warning confirmation: the change remains unsaved. Save again and confirm to
                            keep the earlier date.
                        </li>
                        <li>
                            Return to the order list, select your draft, and choose <strong>Submit</strong> in the
                            selection bar. On the confirmation page, choose <strong>Yes, continue</strong> to submit it
                            for approval. Here, Submit starts the workflow; Update on a form saves its fields.
                        </li>
                    </ol>
                    <p class="callout">
                        <strong>Expected result:</strong> the clerk can still read the submitted order, but its
                        <strong>Update</strong> action is gone. The supervisor must approve it.
                    </p>
                    <h3>If the proposal changes</h3>
                    <p>
                        Other visitors may change stock, prices, or orders while you work. Choose
                        <strong>Reload proposals</strong> and review it again. If existing orders now cover the
                        threshold, repeat the supervisor's target calculation with the latest quantities. If the preview
                        reports an inactive product or warehouse, choose another stock item. An inventory role can
                        correct an inactive or unapproved supplier through <strong>Suppliers</strong>. No instance reset
                        is needed.
                    </p>
                </section>

                <section id="approve">
                    <p class="role">Step 3 / Inventory supervisor</p>
                    <h2>Approve the order</h2>
                    <ol>
                        <li>
                            Switch to <strong>Inventory supervisor</strong>. Open <strong>Purchase Orders</strong> and
                            find the reference you recorded. Select the submitted order, choose
                            <strong>Approve</strong>, then confirm with <strong>Yes, continue</strong>.
                        </li>
                        <li>
                            Return to <strong>Inventory Records</strong>, select the same stock item, and choose
                            <strong>Replenish</strong>. The order quantity has moved from <strong>Pending</strong> to
                            <strong>Incoming</strong>. The preview explains that existing orders cover the threshold and
                            proposes no further purchase.
                        </li>
                        <li>
                            The item still appears under <strong>Below reorder</strong>, because that queue compares
                            on-hand stock with the threshold. Approval covers the purchasing requirement; it does not
                            record a physical delivery.
                        </li>
                    </ol>
                    <p class="callout">
                        <strong>Try rejection instead:</strong> choose <strong>Reject</strong> on a submitted order. It
                        returns to <strong>Draft</strong>, and the clerk can update and submit it again. Only the
                        supervisor can approve or reject an order.
                    </p>
                </section>

                <section id="warnings">
                    <p class="role">Optional / Inventory supervisor</p>
                    <h2>Try a stock-count warning</h2>
                    <p>
                        Update the same inventory record. Note its original <strong>Quantity on hand</strong>, then
                        enter one unit above <strong>Max stock level</strong> and save. The warning asks you to confirm
                        the count. Cancel to leave stored stock unchanged. To try confirmation too, save again and
                        confirm, then restore the original quantity. Both stock and delivery warnings are advisory:
                        confirmation permits the save.
                    </p>
                </section>

                <section id="explore">
                    <h2>Explore more of the demo</h2>
                    <h3>Dashboards and reports</h3>
                    <p>
                        Compare the supervisor and sales associate accounts. Tiles follow each role's read permissions
                        and open filtered lists. Purchasing reports are available to the inventory roles and accountant.
                        Change a chart's period, then follow a chart link to its matching orders.
                    </p>
                    <h3>Order totals</h3>
                    <p>
                        Filter Purchase Orders by supplier and watch the <strong>Order value</strong> footer follow the
                        entire filtered result, not just the visible page. Values have no currency designation because
                        the catalog does not store one.
                    </p>
                    <h3>Suppliers and prices</h3>
                    <p>
                        Either inventory role can update supplier details, including multiple notification email
                        addresses, approval, and typical lead time. <strong>Supplier Prices</strong> supplies default
                        prices for new order lines. Changing a line's price does not change its supplier price, and
                        changing a supplier price does not rewrite existing orders.
                    </p>
                    <h3>Read-only browsing</h3>
                    <p>
                        Use either sales account to explore promotions and their date ranges, or the accountant to see
                        both suppliers and promotions without write actions. Widgets, categories, variants, warehouses,
                        and promotions are read-only for all demo accounts.
                    </p>
                    <p>
                        To learn how to build with these features, visit <a href="https://vueda.dev/">VUEDA</a> and its
                        <a href="https://vueda.dev/v3/">documentation</a>.
                    </p>
                </section>
            </article>
        </div>
    </main>
</template>

<style scoped>
.guide section {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    scroll-margin-top: 2rem;
}
.guide h2 {
    font-size: 1.5rem;
    font-weight: 600;
    line-height: 1.3;
}
.guide h3 {
    margin-top: 1.5rem;
    font-size: 1.125rem;
    font-weight: 600;
}
.guide p,
.guide ol {
    margin-top: 1rem;
}
.guide ol {
    list-style: decimal;
    padding-left: 1.5rem;
}
.guide li {
    padding-left: 0.25rem;
    margin-top: 1rem;
}
.guide a {
    text-decoration: underline;
    text-underline-offset: 0.25em;
}
.guide code {
    overflow-wrap: anywhere;
}
.guide .role {
    margin-top: 0;
    margin-bottom: 0.5rem;
    color: var(--muted-foreground);
    font-size: 0.875rem;
    font-weight: 500;
}
.guide .callout {
    border-left: 2px solid var(--primary);
    padding-left: 1rem;
}
</style>
