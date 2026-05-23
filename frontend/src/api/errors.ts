export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

export class NetworkError extends Error {
  constructor(message = "네트워크 연결을 확인해주세요") {
    super(message);
    this.name = "NetworkError";
  }
}
