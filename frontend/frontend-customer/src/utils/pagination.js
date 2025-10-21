// utils/pagination.js
export const getNextPageNumber = (nextUrl) => {
    return getPageNumberFromUrl(nextUrl);
};

export const getPreviousPageNumber = (previousUrl) => {
    return getPageNumberFromUrl(previousUrl);
};

export const hasNextPage = (pagination) => {
    return pagination?.next !== null;
};

export const hasPreviousPage = (pagination) => {
    return pagination?.previous !== null;
};

export const getTotalPages = (pagination, pageSize = 20) => {
    if (!pagination?.count) return 0;
    return Math.ceil(pagination.count / pageSize);
};