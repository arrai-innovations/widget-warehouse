<script setup>
import Button from "@vueda/controls/button/Button.vue";
import ViewSignIn from "@vueda/views/ViewSignIn.vue";
import WidgetTextInput from "@vueda/widgets/WidgetTextInput.vue";

/**
 * Widget Warehouse sign-in view. Adopts VUEDA's default ViewSignIn (AuthorizingForm
 * chrome, email and password fields, post-login routing, and MFA detection) and
 * customizes only the input styling through the widget slots, demonstrating the
 * slot-based customization surface without re-implementing the sign-in flow.
 *
 * The demo credential panel is added through AuthorizingForm's forwarded `suffix` slot,
 * and fills the form through the context emitted by `form-context` rather than through
 * a second copy of the form state. Widget Warehouse is a public demo, so the panel is
 * not gated on DEBUG: an evaluator on the deployed instance needs it to switch roles.
 */

// Mirrors the roles in server/widget_warehouse/catalog/management/commands/seed_demo_users.py.
// Every account there shares one password so switching roles stays a two-click operation.
const DEMO_PASSWORD = "widget-demo";
const DEMO_ACCOUNTS = [
    { role: "Inventory clerk", email: "clerk@widgetwarehouse.com" },
    { role: "Inventory supervisor", email: "supervisor@widgetwarehouse.com" },
    { role: "Sales associate", email: "associate@widgetwarehouse.com" },
    { role: "Sales manager", email: "manager@widgetwarehouse.com" },
    { role: "Accountant", email: "accountant@widgetwarehouse.com" },
];

// ViewSignIn emits its form context on mount. The context keeps state readonly for
// observation and exposes mutation methods for controlled programmatic updates.
let formContext = null;

function handleFormContext(context) {
    formContext = context;
}

function useAccount(email) {
    if (!formContext) return;
    formContext.updateValue("email", email);
    formContext.updateValue("password", DEMO_PASSWORD);
}
</script>

<template>
    <ViewSignIn @form-context="handleFormContext">
        <template #widget(email)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
        <template #widget(password)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
        <template #suffix>
            <!-- A rule, not a nested card: the panel already sits inside AuthorizingForm's card. -->
            <div class="mt-4 border-t-hairline pt-4">
                <p class="text-[length:var(--vueda-text-supporting)] font-medium">Demo accounts</p>
                <p class="mt-1 text-[length:var(--vueda-text-supporting)] leading-[1.4] text-muted-foreground">
                    Every account below uses the password
                    <span class="font-mono">{{ DEMO_PASSWORD }}</span
                    >. Pick one to fill the form, then sign in. Each role sees a different slice of the catalog.
                </p>
                <ul class="mt-3 flex flex-col gap-1">
                    <li v-for="account in DEMO_ACCOUNTS" :key="account.email">
                        <Button emphasis="ghost" type="button" class="w-full" @click="useAccount(account.email)">
                            <!-- Button centers its content; an inner row spreads role and email to the edges. -->
                            <span class="flex w-full items-center justify-between gap-3 text-left">
                                <span>{{ account.role }}</span>
                                <span class="font-mono text-muted-foreground">{{ account.email }}</span>
                            </span>
                        </Button>
                    </li>
                </ul>
            </div>
        </template>
    </ViewSignIn>
</template>
