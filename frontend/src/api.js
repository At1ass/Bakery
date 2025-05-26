import axios from 'axios';

const AUTH_URL = 'http://localhost:8001';
const CATALOG_URL = 'http://localhost:8002';
const ORDER_URL = 'http://localhost:8003';

// Create axios instances with default config
const authApi = axios.create({
    baseURL: AUTH_URL,
    withCredentials: true,  // Enable credentials for CORS
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

const catalogApi = axios.create({
    baseURL: CATALOG_URL,
    withCredentials: true,  // Enable credentials for CORS
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

const orderApi = axios.create({
    baseURL: ORDER_URL,
    withCredentials: true,  // Enable credentials for CORS
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

// Add response interceptor to handle 401 errors
const handleUnauthorized = (error) => {
    if (error.response && error.response.status === 401) {
        // Clear token and redirect to login
        localStorage.removeItem('token');
        window.location.reload();
    }
    return Promise.reject(error);
};

authApi.interceptors.response.use((response) => response, handleUnauthorized);
catalogApi.interceptors.response.use((response) => response, handleUnauthorized);
orderApi.interceptors.response.use((response) => response, handleUnauthorized);

export async function login(email, password) {
    const response = await authApi.post('/login', 
        new URLSearchParams({ username: email, password }), 
        { 
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            validateStatus: function (status) {
                return status >= 200 && status < 500;
            }
        }
    );
    
    if (response.status !== 200) {
        throw { 
            response: response,
            message: response.data?.detail || 'Login failed'
        };
    }

    if (!response.data || !response.data.access_token) {
        throw new Error('Invalid response format: missing access token');
    }
    
    return response.data;
}

export async function register(email, password, role = 'user') {
    const response = await authApi.post('/register', 
        { email, password, role },
        {
            validateStatus: function (status) {
                return status >= 200 && status < 500;
            }
        }
    );
    
    if (response.status !== 201 && response.status !== 200) {
        throw { 
            response: response,
            message: response.data?.detail || 'Registration failed'
        };
    }

    if (!response.data || !response.data.email) {
        throw new Error('Invalid response format: missing user data');
    }
    
    return response.data;
}

export async function fetchProducts(token) {
    try {
        const config = {
            headers: {
                'Accept': 'application/json'
            }
        };
        
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await catalogApi.get('/products', config);
        console.log('Raw API response:', response);
        
        if (!response.data) {
            console.warn('No data received from server');
            return { data: [] };
        }
        
        // Handle different response formats
        let products;
        if (Array.isArray(response.data)) {
            products = response.data;
        } else if (typeof response.data === 'object') {
            if (response.data.data && Array.isArray(response.data.data)) {
                products = response.data.data;
            } else if (response.data.products && Array.isArray(response.data.products)) {
                products = response.data.products;
            } else {
                console.warn('Unexpected data format:', response.data);
                products = [];
            }
        } else {
            console.warn('Invalid data type:', typeof response.data);
            products = [];
        }
                        
        console.log('Processed products array:', products);
        return { data: products };
    } catch (error) {
        console.error('Error fetching products:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status,
            headers: error.response?.headers
        });
        throw error;
    }
}

export async function createProduct(token, product) {
    if (!token) {
        throw new Error('No token provided');
    }

    try {
        const response = await catalogApi.post('/products', product, {
            headers: { 
                Authorization: `Bearer ${token}`,
                'Accept': 'application/json'
            }
        });
        
        if (!response.data) {
            throw new Error('No data received from server');
        }
        
        return response;
    } catch (error) {
        console.error('Error creating product:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        throw error;
    }
}

export async function updateProduct(token, productId, product) {
    if (!token) {
        throw new Error('No token provided');
    }

    try {
        const response = await catalogApi.put(`/products/${productId}`, product, {
            headers: { 
                Authorization: `Bearer ${token}`,
                'Accept': 'application/json'
            }
        });
        
        if (!response.data) {
            throw new Error('No data received from server');
        }
        
        return response;
    } catch (error) {
        console.error('Error updating product:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        throw error;
    }
}

export async function deleteProduct(token, productId) {
    if (!token) {
        throw new Error('No token provided');
    }

    try {
        const response = await catalogApi.delete(`/products/${productId}`, {
            headers: { 
                Authorization: `Bearer ${token}`,
                'Accept': 'application/json'
            }
        });
        return response;
    } catch (error) {
        console.error('Error deleting product:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        throw error;
    }
}

export async function createOrder(token, order) {
    try {
        const response = await orderApi.post('/orders', order, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response;
    } catch (error) {
        console.error('Error creating order:', error);
        throw error;
    }
}

export async function fetchOrders(token) {
    try {
        const response = await orderApi.get('/orders', {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response;
    } catch (error) {
        console.error('Error fetching orders:', error);
        throw error;
    }
}

export async function getCurrentUser(token) {
    if (!token) {
        throw new Error('No token provided');
    }

    try {
        const response = await authApi.get('/me', {
            headers: { 
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.data || !response.data.email) {
            throw new Error('Invalid response format: missing user data');
        }

        return response;
    } catch (error) {
        console.error('Error getting current user:', error);
        throw error;
    }
}

export async function refreshToken(token) {
    const response = await authApi.post('/refresh', null, { 
        headers: { Authorization: `Bearer ${token}` },
        validateStatus: function (status) {
            return status >= 200 && status < 500;
        }
    });

    if (response.status !== 200) {
        throw {
            response: response,
            message: response.data?.detail || 'Token refresh failed'
        };
    }

    if (!response.data || !response.data.access_token) {
        throw new Error('Invalid response format: missing access token');
    }

    return response.data.access_token;
}
