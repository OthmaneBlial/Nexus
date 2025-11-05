import { createServer } from "node:http";

import { createApp } from "./app.js";

const PORT = Number.parseInt(process.env.PORT ?? "4000", 10);

const app = createApp();
const server = createServer(app);

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Node TODO API listening on http://localhost:${PORT}`);
});
