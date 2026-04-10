import "./index.css";
import TheApp from "./TheApp.vue";
import { getRouter } from "./router/index.js";
import vuedaTailwind from "@vueda/theme/vueda-tailwind/index.js";
import { setTheme } from "@vueda/use/useTheme.js";
import { setupDefaultListCrud } from "@vueda/utils/listCrud.js";
import { setupDefaultObjectCrud } from "@vueda/utils/objectCrud.js";
import { createPinia } from "pinia";
import { createApp } from "vue";

setTheme(vuedaTailwind);
setupDefaultListCrud();
setupDefaultObjectCrud();

const app = createApp(TheApp);
const pinia = createPinia();
const router = getRouter(app, pinia);

app.use(pinia);
app.use(router);

app.mount("#the-app");

export default app;
