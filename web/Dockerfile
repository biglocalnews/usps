FROM node:18

WORKDIR /code

COPY .yarnrc.yml .npmrc yarn.lock package.json /code/

RUN yarn install

COPY . /code

RUN yarn build

CMD ["node", "-r", "dotenv/config", "build"]
