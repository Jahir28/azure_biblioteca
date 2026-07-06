<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const API_URL =
  import.meta.env.VITE_API_URL ||
  '/api'

const metrics = ref({})
const books = ref([])
const users = ref([])
const loans = ref([])
const activeTab = ref('books')
const error = ref('')
const loading = ref(false)

const emptyBook = { id: null, title: '', author: '', isbn: '', year: '', available: true }
const emptyUser = { id: null, name: '', email: '', phone: '' }
const emptyLoan = { id: null, book_id: '', user_id: '', loan_date: today(), due_date: today(), returned: false }

const bookForm = reactive({ ...emptyBook })
const userForm = reactive({ ...emptyUser })
const loanForm = reactive({ ...emptyLoan })

const availableBooks = computed(() => books.value.filter((book) => book.available || book.id === Number(loanForm.book_id)))
const activeLoans = computed(() => loans.value.filter((loan) => !loan.returned))

function today() {
  return new Date().toISOString().slice(0, 10)
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || `Error HTTP ${response.status}`)
  }
  if (response.status === 204) return null
  return response.json()
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [metricsData, booksData, usersData, loansData] = await Promise.all([
      request('/metrics'),
      request('/books'),
      request('/users'),
      request('/loans')
    ])
    metrics.value = metricsData
    books.value = booksData
    users.value = usersData
    loans.value = loansData
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function resetForm(target, source) {
  Object.assign(target, source)
}

async function saveBook() {
  const payload = {
    title: bookForm.title,
    author: bookForm.author,
    isbn: bookForm.isbn || null,
    year: bookForm.year ? Number(bookForm.year) : null
  }
  await saveEntity('/books', bookForm.id, payload, () => resetForm(bookForm, emptyBook))
}

async function saveUser() {
  await saveEntity('/users', userForm.id, { name: userForm.name, email: userForm.email, phone: userForm.phone || null }, () =>
    resetForm(userForm, emptyUser)
  )
}

async function saveLoan() {
  const payload = {
    book_id: Number(loanForm.book_id),
    user_id: Number(loanForm.user_id),
    loan_date: loanForm.loan_date,
    due_date: loanForm.due_date,
    returned: loanForm.returned
  }
  await saveEntity('/loans', loanForm.id, payload, () => resetForm(loanForm, { ...emptyLoan, loan_date: today(), due_date: today() }))
}

async function saveEntity(path, id, payload, reset) {
  error.value = ''
  try {
    await request(id ? `${path}/${id}` : path, {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(payload)
    })
    reset()
    await loadAll()
  } catch (err) {
    error.value = err.message
  }
}

function editBook(book) {
  Object.assign(bookForm, { ...book, year: book.year || '' })
}

function editUser(user) {
  Object.assign(userForm, user)
}

function editLoan(loan) {
  Object.assign(loanForm, { ...loan, book_id: String(loan.book_id), user_id: String(loan.user_id) })
}

async function removeEntity(path, id) {
  error.value = ''
  try {
    await request(`${path}/${id}`, { method: 'DELETE' })
    await loadAll()
  } catch (err) {
    error.value = err.message
  }
}

function bookName(id) {
  return books.value.find((book) => book.id === id)?.title || `Libro #${id}`
}

function userName(id) {
  return users.value.find((user) => user.id === id)?.name || `Usuario #${id}`
}

onMounted(loadAll)
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Biblioteca</p>
        <h1>Azure Biblioteca</h1>
        <p class="subtitle">Panel operativo para libros, usuarios y prestamos.</p>
      </div>
      <button class="secondary refresh" :disabled="loading" @click="loadAll">{{ loading ? 'Actualizando' : 'Actualizar' }}</button>
    </header>

    <section class="metrics" aria-label="Metricas principales">
      <article class="metric total">
        <span class="metric-icon">LB</span>
        <div>
          <span>Total libros</span>
          <strong>{{ metrics.total_books ?? 0 }}</strong>
        </div>
      </article>
      <article class="metric available">
        <span class="metric-icon">OK</span>
        <div>
          <span>Disponibles</span>
          <strong>{{ metrics.available_books ?? 0 }}</strong>
        </div>
      </article>
      <article class="metric loaned">
        <span class="metric-icon">PR</span>
        <div>
          <span>Prestados</span>
          <strong>{{ metrics.loaned_books ?? 0 }}</strong>
        </div>
      </article>
      <article class="metric users">
        <span class="metric-icon">US</span>
        <div>
          <span>Usuarios</span>
          <strong>{{ metrics.registered_users ?? 0 }}</strong>
        </div>
      </article>
      <article class="metric active-loans">
        <span class="metric-icon">AC</span>
        <div>
          <span>Prestamos activos</span>
          <strong>{{ metrics.active_loans ?? 0 }}</strong>
        </div>
      </article>
    </section>

    <p v-if="error" class="alert">{{ error }}</p>

    <nav class="tabs" aria-label="Secciones">
      <button :class="{ active: activeTab === 'books' }" @click="activeTab = 'books'">Libros</button>
      <button :class="{ active: activeTab === 'users' }" @click="activeTab = 'users'">Usuarios</button>
      <button :class="{ active: activeTab === 'loans' }" @click="activeTab = 'loans'">Prestamos</button>
    </nav>

    <section v-if="activeTab === 'books'" class="workspace">
      <form class="panel" @submit.prevent="saveBook">
        <div class="panel-heading">
          <h2>{{ bookForm.id ? 'Editar libro' : 'Nuevo libro' }}</h2>
          <p>Inventario bibliografico</p>
        </div>
        <label>Titulo<input v-model="bookForm.title" required /></label>
        <label>Autor<input v-model="bookForm.author" required /></label>
        <label>ISBN<input v-model="bookForm.isbn" /></label>
        <label>Anio<input v-model="bookForm.year" type="number" min="0" /></label>
        <p class="field-note">El estado del libro se actualiza automaticamente con los prestamos.</p>
        <div class="actions">
          <button type="submit">Guardar</button>
          <button type="button" class="secondary" @click="resetForm(bookForm, emptyBook)">Limpiar</button>
        </div>
      </form>

      <div class="table-wrap">
        <div class="table-title">
          <h2>Libros registrados</h2>
          <span>{{ books.length }} registros</span>
        </div>
        <div v-if="!books.length" class="empty-state">
          <strong>No hay libros registrados</strong>
          <span>Agrega el primer libro desde el formulario.</span>
        </div>
        <table v-else>
          <thead><tr><th>Titulo</th><th>Autor</th><th>ISBN</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            <tr v-for="book in books" :key="book.id">
              <td>{{ book.title }}</td>
              <td>{{ book.author }}</td>
              <td>{{ book.isbn || '-' }}</td>
              <td><span :class="['status', book.available ? 'ok' : 'busy']">{{ book.available ? 'Disponible' : 'Prestado' }}</span></td>
              <td class="row-actions">
                <button class="secondary" @click="editBook(book)">Editar</button>
                <button class="danger" @click="removeEntity('/books', book.id)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="activeTab === 'users'" class="workspace">
      <form class="panel" @submit.prevent="saveUser">
        <div class="panel-heading">
          <h2>{{ userForm.id ? 'Editar usuario' : 'Nuevo usuario' }}</h2>
          <p>Registro de lectores</p>
        </div>
        <label>Nombre<input v-model="userForm.name" required /></label>
        <label>Email<input v-model="userForm.email" type="email" required /></label>
        <label>Telefono<input v-model="userForm.phone" /></label>
        <div class="actions">
          <button type="submit">Guardar</button>
          <button type="button" class="secondary" @click="resetForm(userForm, emptyUser)">Limpiar</button>
        </div>
      </form>

      <div class="table-wrap">
        <div class="table-title">
          <h2>Usuarios registrados</h2>
          <span>{{ users.length }} registros</span>
        </div>
        <div v-if="!users.length" class="empty-state">
          <strong>No hay usuarios registrados</strong>
          <span>Agrega un usuario para poder crear prestamos.</span>
        </div>
        <table v-else>
          <thead><tr><th>Nombre</th><th>Email</th><th>Telefono</th><th></th></tr></thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.phone || '-' }}</td>
              <td class="row-actions">
                <button class="secondary" @click="editUser(user)">Editar</button>
                <button class="danger" @click="removeEntity('/users', user.id)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="activeTab === 'loans'" class="workspace">
      <form class="panel" @submit.prevent="saveLoan">
        <div class="panel-heading">
          <h2>{{ loanForm.id ? 'Editar prestamo' : 'Nuevo prestamo' }}</h2>
          <p>Control de circulacion</p>
        </div>
        <label>Libro disponible
          <select v-model="loanForm.book_id" required>
            <option value="" disabled>Seleccionar</option>
            <option v-for="book in availableBooks" :key="book.id" :value="book.id">{{ book.title }}</option>
          </select>
        </label>
        <p v-if="availableBooks.length" class="field-note">Solo aparecen libros que no tienen un prestamo activo.</p>
        <p v-else class="field-note warning">No hay libros disponibles para prestar en este momento.</p>
        <label>Usuario
          <select v-model="loanForm.user_id" required>
            <option value="" disabled>Seleccionar</option>
            <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
          </select>
        </label>
        <label>Fecha prestamo<input v-model="loanForm.loan_date" type="date" required /></label>
        <label>Fecha devolucion<input v-model="loanForm.due_date" type="date" required /></label>
        <label class="check"><input v-model="loanForm.returned" type="checkbox" /> Devuelto</label>
        <div class="actions">
          <button type="submit">Guardar</button>
          <button type="button" class="secondary" @click="resetForm(loanForm, { ...emptyLoan, loan_date: today(), due_date: today() })">Limpiar</button>
        </div>
      </form>

      <div class="table-wrap">
        <div class="table-title">
          <h2>Historial de prestamos</h2>
          <span>{{ activeLoans.length }} activos</span>
        </div>
        <div v-if="!loans.length" class="empty-state">
          <strong>No hay prestamos registrados</strong>
          <span>Selecciona un libro disponible y un usuario para iniciar.</span>
        </div>
        <table v-else>
          <thead><tr><th>Libro</th><th>Usuario</th><th>Prestamo</th><th>Vence</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            <tr v-for="loan in loans" :key="loan.id">
              <td>{{ loan.book?.title || bookName(loan.book_id) }}</td>
              <td>{{ loan.user?.name || userName(loan.user_id) }}</td>
              <td>{{ loan.loan_date }}</td>
              <td>{{ loan.due_date }}</td>
              <td><span :class="['status', loan.returned ? 'ok' : 'busy']">{{ loan.returned ? 'Devuelto' : 'Activo' }}</span></td>
              <td class="row-actions">
                <button class="secondary" @click="editLoan(loan)">Editar</button>
                <button class="danger" @click="removeEntity('/loans', loan.id)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>
