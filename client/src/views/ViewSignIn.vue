<script setup>
import ViewSignIn from "@vueda/views/ViewSignIn.vue";
import WidgetTextInput from "@vueda/widgets/WidgetTextInput.vue";

/**
 * Widget Warehouse sign-in view. Adopts VUEDA's default ViewSignIn (AuthorizingForm
 * chrome, email and password fields, post-login routing, and MFA detection) and
 * customizes only the input styling through the widget slots, demonstrating the
 * slot-based customization surface without re-implementing the sign-in flow.
 */
</script>

<template>
    <ViewSignIn>
        <template #widget(email)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
        <template #widget(password)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
    </ViewSignIn>
</template>
