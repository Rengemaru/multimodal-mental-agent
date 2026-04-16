FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.html tsconfig.json vite.config.ts vitest.config.ts eslint.config.js .prettierrc ./
COPY public ./public
COPY src ./src

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
