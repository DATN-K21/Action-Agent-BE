const axios = require('axios')

const axiosInstance = axios.create({
	timeout: 5000, // 5 seconds
	headers: {
		'Content-Type': 'application/json',
	},
	withCredentials: true,
})

axiosInstance.interceptors.request.use((config) => {
	// config.headers.Authorization = `Bearer ${tokenInHeader}`;
	return config;
}, (error) => {
	return Promise.reject(error);
});

//RESPONSE
axiosInstance.interceptors.response.use((response) => {
	return response?.data;
}, (err) => {
	const data = err?.response?.data;
	const msg = data?.message;

	return Promise.reject(data ?? new Error(msg ?? err.message));
});


module.exports = axiosInstance;