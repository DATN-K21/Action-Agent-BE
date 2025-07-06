import axios from 'axios';
import { EnvironmentConfig } from './environment.config';

const AiServiceAxiosInstance = axios.create({
    baseURL: EnvironmentConfig.AI_SERVICE_URL,
});

AiServiceAxiosInstance.interceptors.response.use(
    (response) => {
        // Handle successful responses
        return response?.data ?? response;
    },
    (error) => {
        // Handle errors
        return Promise.reject(error);
    }
)

export { AiServiceAxiosInstance };

