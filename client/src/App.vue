<template>
  <header>
    <nav class="container">
      <router-link to="/" class="logo">
        Video Platform
      </router-link>
    </nav>
  </header>

  <router-view />
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
@import '@/assets/main.css';

header {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

nav {
  padding: 1rem 0;
}

.logo {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--primary-color);
  text-decoration: none;
}

.logo:hover {
  color: var(--primary-hover);
}
</style>
