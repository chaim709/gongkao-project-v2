import 'axios';

// 覆盖 axios 类型：因为 client.ts 的响应拦截器已经解包了 response.data
// 所以实际返回值是 T 而不是 AxiosResponse<T>
declare module 'axios' {
  export interface AxiosInstance {
    request<T = any, D = any>(config: AxiosRequestConfig<D>): Promise<T>;
    get<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>;
    delete<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>;
    head<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>;
    options<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>;
    post<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>;
    put<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>;
    patch<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>;
    postForm<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>;
    putForm<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>;
    patchForm<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>;
  }
}
