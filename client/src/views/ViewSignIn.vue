<script setup>
import { faCloudMoon, faSunBright } from "@fortawesome/sharp-duotone-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Button from "@vueda/controls/button/Button.vue";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import ViewSignIn from "@vueda/views/ViewSignIn.vue";
import WidgetTextInput from "@vueda/widgets/WidgetTextInput.vue";

/**
 * Widget Warehouse sign-in view. Adopts VUEDA's default ViewSignIn (AuthorizingForm
 * chrome, email and password fields, post-login routing, and MFA detection) and
 * customizes only the input styling through the widget slots, demonstrating the
 * slot-based customization surface without re-implementing the sign-in flow.
 *
 * The sign-in route renders outside the sidebar shell (see TheApp.vue's guest routes),
 * so the dark-mode toggle that normally lives in the sidebar has nowhere else to go;
 * it rides in above the card via AuthorizingForm's `auth-form-prefix-header` slot.
 */
const darkModeStore = storeDarkMode();
</script>

<template>
    <ViewSignIn>
        <template #auth-form-prefix-header>
            <div class="flex w-full justify-end sm:w-[35rem]">
                <Button emphasis="ghost" size="icon-sm" aria-label="Toggle color mode" @click="darkModeStore.toggle()">
                    <FontAwesomeIcon :icon="darkModeStore.isDark ? faSunBright : faCloudMoon" fixed-width />
                </Button>
            </div>
        </template>
        <template #widget(email)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
        <template #widget(password)="slotProps">
            <WidgetTextInput v-bind="slotProps" class="font-mono" />
        </template>
    </ViewSignIn>
</template>
