import TheApp from "./TheApp.vue";
import { getRouter } from "./router/index.js";
import vuedaTailwind from "@vueda/theme/vueda-tailwind/index.js";
import { setIcons } from "@vueda/use/useIcons.js";
import { setTheme } from "@vueda/use/useTheme.js";
import { setupDefaultListCrud } from "@vueda/utils/listCrud.js";
import { setupDefaultObjectCrud } from "@vueda/utils/objectCrud.js";
import { createPinia } from "pinia";
import { createApp } from "vue";

import { phosphorIcons } from "@/icons.js";
import { setupModelConfig } from "@/setupModelConfig.js";

setTheme(vuedaTailwind);
setIcons(phosphorIcons);
setupDefaultListCrud();
setupDefaultObjectCrud();

const app = createApp(TheApp);
const pinia = createPinia();

app.use(pinia);
setupModelConfig(pinia);

const router = getRouter(app, pinia);

app.use(router);

app.mount("#the-app");

export default app;
