# USPS UI

## Developing

### Environment

See `../secrets/node_env.dev` for environment variables.

To run a local dev server, create a `.env` file in this directory with your secrets.

### Dev server

Run the development server and open the app.

```bash
yarn dev --open

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
yarn build
```

## Deployment

Built as a NodeJS (SSR) service running in a Docker container.

### Environment

Override the dev secrets with production-quality values.
