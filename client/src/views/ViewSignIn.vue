<script setup>
import FormChores from "@vueda/components/FormChores.vue";
import Button from "@vueda/controls/button/Button.vue";
import FormField from "@vueda/fields/FormField.vue";
import Card from "@vueda/shell/card/Card.vue";
import CardContent from "@vueda/shell/card/CardContent.vue";
import CardDescription from "@vueda/shell/card/CardDescription.vue";
import CardFooter from "@vueda/shell/card/CardFooter.vue";
import CardHeader from "@vueda/shell/card/CardHeader.vue";
import CardTitle from "@vueda/shell/card/CardTitle.vue";
import { storeUser } from "@vueda/stores/storeUser.js";
import { useSignInFlow } from "@vueda/use/useSignInFlow.js";
import { FormValidationError } from "@vueda/utils/errors.js";
import WidgetTextInput from "@vueda/widgets/WidgetTextInput.vue";
import { ref } from "vue";
import { toast } from "vue-sonner";

const { formContext } = useSignInFlow({
    formProps: { initialValues: { email: "", password: "" } },
});

const userStore = storeUser();
const loading = ref(false);

const handleSubmit = async () => {
    loading.value = true;
    try {
        await userStore.login({
            email: formContext.state.values.email,
            password: formContext.state.values.password,
        });
    } catch (error) {
        if (error instanceof FormValidationError) {
            formContext.handleServerFormValidationError(error);
        } else {
            toast.error("Sign In Failed", { duration: 15000 });
        }
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <div class="flex min-h-full justify-center items-center">
        <div class="flex flex-col max-w-full">
            <form @submit.prevent="handleSubmit">
                <FormChores />
                <Card class="sm:w-140 max-w-full">
                    <CardHeader>
                        <CardTitle>Sign In</CardTitle>
                        <CardDescription>Enter your email and password below to login to your account</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <FormField name="email" label="Email">
                            <WidgetTextInput class="font-mono" />
                        </FormField>
                        <FormField name="password" label="Password">
                            <WidgetTextInput class="font-mono" type="password" />
                        </FormField>
                    </CardContent>
                    <CardFooter>
                        <Button type="submit" :disabled="loading">Sign In</Button>
                    </CardFooter>
                </Card>
            </form>
        </div>
    </div>
</template>
