<script setup>
import Button from "@vueda/controls/button/Button.vue";
import { storeUser } from "@vueda/stores/storeUser.js";
import { useTitle } from "@vueuse/core";
import { RouterLink } from "vue-router";

const userStore = storeUser();
useTitle("Widget Warehouse | A VUEDA demo");
</script>

<template>
    <main class="mx-auto max-w-6xl px-5 pt-32 pb-16 sm:px-8">
        <section aria-labelledby="intro-title" class="grid gap-10 pb-12 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
            <div>
                <p class="mb-4 text-sm font-medium tracking-widest text-muted-foreground uppercase">Django + Vue</p>
                <h1 id="intro-title" class="max-w-xl text-4xl leading-tight font-bold tracking-tight sm:text-5xl">
                    A working VUEDA demo.
                </h1>
                <p class="mt-6 max-w-xl text-lg leading-relaxed">
                    Explore an inventory and purchasing application built with VUEDA. Browse the catalog, create a
                    purchase order, and switch roles to see who can change records and approve orders.
                </p>
                <p class="mt-4 max-w-xl text-base leading-relaxed text-muted-foreground">
                    VUEDA turns Django models, serializers, and viewsets into Vue forms, lists, and detail screens.
                    Widget Warehouse combines those generated screens with custom layouts, reports, and a replenishment
                    action.
                </p>
                <div class="mt-8 flex flex-wrap gap-3">
                    <Button as-child tone="primary" size="lg">
                        <RouterLink :to="{ name: userStore.loggedIn ? 'dashboard' : 'sign-in' }">
                            {{ userStore.loggedIn ? "Return to dashboard" : "Explore the demo" }}
                        </RouterLink>
                    </Button>
                    <Button as-child emphasis="outline" size="lg">
                        <RouterLink :to="{ name: 'walkthrough' }">Follow the walkthrough</RouterLink>
                    </Button>
                </div>
                <a href="https://vueda.dev/" class="mt-6 inline-block text-sm underline underline-offset-4">
                    Learn about VUEDA
                </a>
            </div>
            <aside aria-labelledby="scenario-title" class="border-hairline bg-muted/30 p-6 sm:p-8">
                <p class="text-sm font-medium text-muted-foreground">The walkthrough</p>
                <h2 id="scenario-title" class="mt-2 text-2xl font-semibold tracking-tight">
                    From a stock shortage to an approved order
                </h2>
                <ol class="mt-6 space-y-6">
                    <li class="border-l-2 border-primary pl-4">
                        <p class="text-xs font-medium tracking-wide text-muted-foreground uppercase">1 / Supervisor</p>
                        <p class="mt-1 text-base">Set a stock target that creates a shortage.</p>
                    </li>
                    <li class="border-l-2 border-primary pl-4">
                        <p class="text-xs font-medium tracking-wide text-muted-foreground uppercase">2 / Clerk</p>
                        <p class="mt-1 text-base">Create a replenishment order and submit it for approval.</p>
                    </li>
                    <li class="border-l-2 border-primary pl-4">
                        <p class="text-xs font-medium tracking-wide text-muted-foreground uppercase">3 / Supervisor</p>
                        <p class="mt-1 text-base">Approve the order and see pending stock become incoming stock.</p>
                    </li>
                </ol>
            </aside>
        </section>

        <section aria-labelledby="features-title" class="border-t-hairline py-10">
            <h2 id="features-title" class="text-2xl font-semibold tracking-tight">What to look for</h2>
            <div class="mt-6 grid gap-8 md:grid-cols-3">
                <article>
                    <h3 class="text-lg font-semibold">Forms and lists</h3>
                    <p class="mt-2 text-base leading-relaxed text-muted-foreground">
                        Filter inventory, edit order lines in a table, and confirm advisory warnings before saving. List
                        totals follow the whole filtered result.
                    </p>
                </article>
                <article>
                    <h3 class="text-lg font-semibold">Permissions and workflows</h3>
                    <p class="mt-2 text-base leading-relaxed text-muted-foreground">
                        A clerk can prepare an order but cannot approve it. Submitting the draft removes the clerk's
                        update action. The server enforces these permissions, not just the interface.
                    </p>
                </article>
                <article>
                    <h3 class="text-lg font-semibold">Application customization</h3>
                    <p class="mt-2 text-base leading-relaxed text-muted-foreground">
                        Explore a custom dashboard, purchasing charts, sectioned forms, and a bulk replenishment action
                        alongside VUEDA's standard views.
                    </p>
                </article>
            </div>
        </section>

        <section aria-labelledby="shared-title" class="border-t-hairline pt-8">
            <h2 id="shared-title" class="text-lg font-semibold">A shared demo, not a production warehouse</h2>
            <p class="mt-2 max-w-3xl text-base leading-relaxed text-muted-foreground">
                Demo accounts are public. Other visitors can change the same records, and operator resets discard demo
                changes. Use sample data only. Approval covers a purchasing requirement; receiving an order changes its
                workflow state but does not increase on-hand stock.
            </p>
            <p class="mt-5 text-sm">
                Building your own application?
                <a href="https://vueda.dev/v3/" class="underline underline-offset-4">Read the VUEDA documentation.</a>
            </p>
        </section>
    </main>
</template>
