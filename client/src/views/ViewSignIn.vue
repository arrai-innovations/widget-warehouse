<script setup>
import AuthorizingForm from "@vueda/components/AuthorizingForm.vue";
import Button from "@vueda/controls/button/Button.vue";
import FormField from "@vueda/fields/FormField.vue";
import { storeUser } from "@vueda/stores/storeUser.js";
import WidgetTextInput from "@vueda/widgets/WidgetTextInput.vue";

const userStore = storeUser();

function login({ formValues }) {
    return userStore.login(formValues);
}
</script>

<template>
    <AuthorizingForm header="Sign In" :run-action="login">
        <template #action-form-inner>
            <FormField name="email" label="Email" required>
                <WidgetTextInput />
            </FormField>
            <FormField name="password" label="Password" required>
                <WidgetTextInput type="password" />
            </FormField>
        </template>
        <template #action-bar>
            <Button type="submit">Sign In</Button>
        </template>
    </AuthorizingForm>
</template>
