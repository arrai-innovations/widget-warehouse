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
 * and fills the form through the `form-object` event rather than through a second copy
 * of the form state. Widget Warehouse is a public demo, so the panel is not gated on
 * DEBUG: an evaluator on the deployed instance needs it to switch roles.
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

// AuthorizingForm emits a ref to its live form values on mount. Holding that ref is what
// lets a credential row write into the real form state instead of shadowing it. A plain
// binding rather than a ref: the click handler reads it imperatively, and a ref assigned
// into another ref's value is not unwrapped, which would bury the form values one level
// deeper than the writes below expect.
let formValues = null;

function handleFormObject(values) {
    formValues = values;
}

function useAccount(email) {
    if (!formValues?.value) return;
    formValues.value.email = email;
    formValues.value.password = DEMO_PASSWORD;
}
</script>

<template>
    <ViewSignIn @form-object="handleFormObject">
        <template #widget(email)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
        <template #widget(password)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
        <template #suffix>
            <div class="mt-4 rounded hairline hairline-border bg-muted/25 p-4">
                <p class="text-[length:var(--vueda-text-supporting)] font-medium">Demo accounts</p>
                <p class="mt-1 text-[length:var(--vueda-text-supporting)] leading-[1.4] text-muted-foreground">
                    Every account below uses the password
                    <span class="font-mono">{{ DEMO_PASSWORD }}</span
                    >. Pick one to fill the form, then sign in. Each role sees a different slice of the catalog.
                </p>
                <ul class="mt-3 flex flex-col gap-1">
                    <li v-for="account in DEMO_ACCOUNTS" :key="account.email">
                        <Button
                            emphasis="ghost"
                            type="button"
                            class="w-full justify-between gap-3 text-left"
                            @click="useAccount(account.email)"
                        >
                            <span>{{ account.role }}</span>
                            <span class="font-mono text-muted-foreground">{{ account.email }}</span>
                        </Button>
                    </li>
                </ul>
            </div>
        </template>
    </ViewSignIn>
</template>
