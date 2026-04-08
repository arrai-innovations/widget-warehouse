import TheApp from "./TheApp.vue";
import { getRouter } from "./router/index.js";
import Aura from "@primeuix/themes/aura";
import { setPrimeVuePreset } from "@vueda/theme/register.js";
import { setupDefaultListCrud } from "@vueda/utils/listCrud.js";
import { setupDefaultObjectCrud } from "@vueda/utils/objectCrud.js";
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import ConfirmationService from "primevue/confirmationservice";
import ToastService from "primevue/toastservice";
import Tooltip from "primevue/tooltip";
import { createApp } from "vue";

setupDefaultListCrud();
setupDefaultObjectCrud();

const app = createApp(TheApp);
const pinia = createPinia();
const router = getRouter(app, pinia);

app.use(pinia);
app.use(router);
app.use(PrimeVue, {
    theme: {
        preset: Aura,
    },
});
app.use(ToastService);
app.use(ConfirmationService);
app.directive("tooltip", Tooltip);

setPrimeVuePreset(Aura);

app.mount("#the-app");

export default app;
