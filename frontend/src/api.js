import axios from 'axios';

const AUTH_URL = 'http://localhost:8001';
const CATALOG_URL = 'http://localhost:8002';
const ORDER_URL = 'http://localhost:8003';

export async function login(email, password) {
    const response = await axios.post(`${AUTH_URL}/login`, 
        new URLSearchParams({ username: email, password }), 
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    return response.data;
}

export async function register(email, password, role = 'user') {
    const response = await axios.post(`${AUTH_URL}/register`, { email, password, role });
    return response.data;
}

export async function fetchProducts(token) {
    const response = await axios.get(`${CATALOG_URL}/products`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response;
}

export async function createProduct(token, product) {
    const response = await axios.post(`${CATALOG_URL}/products`, product, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return { data: response.data };  // Match the response format with fetchProducts
}

export async function updateProduct(token, productId, product) {
    const response = await axios.put(`${CATALOG_URL}/products/${productId}`, product, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return { data: response.data };  // Match the response format with fetchProducts
}

export async function deleteProduct(token, productId) {
    await axios.delete(`${CATALOG_URL}/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
}

export async function createOrder(token, order) {
    const response = await axios.post(`${ORDER_URL}/orders`, order, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response;
}

export async function fetchOrders(token) {
    const response = await axios.get(`${ORDER_URL}/orders`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response;
}

export async function getCurrentUser(token) {
    const response = await axios.get(`${AUTH_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response;
}
