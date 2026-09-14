import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ScmService {
  private apiUrl = environment.apiUrl + '/scm-accounts';

  constructor(private http: HttpClient) {}

  getAccounts(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  createAccount(account: { name: string, provider: string, access_token: string }): Observable<any> {
    return this.http.post<any>(this.apiUrl, account);
  }

  registerWebhook(data: { scm_account_id: number, repository_url: string, llm_model?: string }): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/webhooks/register`, data);
  }

  getWebhooks(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/webhooks`);
  }
}
