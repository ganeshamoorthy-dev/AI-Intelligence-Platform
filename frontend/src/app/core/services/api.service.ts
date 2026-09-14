import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface DashboardMetrics {
  total_projects: number;
  active_jobs: number;
  total_issues_found: number;
  avg_latency_ms: number;
  total_tokens_used?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;
  private useMock = environment.enableMock;

  constructor(private http: HttpClient) { }

  getMetrics(): Observable<DashboardMetrics> {
    if (this.useMock) {
      return of({
        total_projects: 3,
        active_jobs: 1,
        total_issues_found: 24,
        avg_latency_ms: 8400,
        total_tokens_used: 1250000
      });
    }
    return this.http.get<DashboardMetrics>(`${this.apiUrl}/dashboard/metrics`).pipe(
      catchError(err => {
        console.error('Failed to load metrics:', err);
        return of({
          total_projects: 0,
          active_jobs: 0,
          total_issues_found: 0,
          avg_latency_ms: 0,
          total_tokens_used: 0
        });
      })
    );
  }

  getRecentJobs(): Observable<any[]> {
    if (this.useMock) {
      return of([
        { id: 101, repo_name: 'test/repo', pr_number: 42, pr_title: 'Fix issue', status: 'completed', commit_sha: 'a1b2c3d', started_at: new Date(Date.now() - 10000).toISOString(), completed_at: new Date().toISOString(), latency_ms: 10000, total_tokens: 4500 },
        { id: 102, repo_name: 'test/repo', pr_number: 43, pr_title: 'Add feature', status: 'processing', commit_sha: 'e4f5g6h', started_at: new Date().toISOString(), completed_at: null, latency_ms: null, total_tokens: null }
      ]);
    }
    return this.http.get<any[]>(`${this.apiUrl}/dashboard/jobs`).pipe(
      catchError(err => {
        console.error('Failed to load jobs:', err);
        return of([]);
      })
    );
  }

  getJobFindings(jobId: number): Observable<any> {
    if (this.useMock) {
      return of({
        pr_metadata: {
          title: 'Implement OAuth Authentication',
          number: 105,
          author: 'dev-user',
          repo_name: 'acme/auth-service',
          status: 'completed',
          commit_sha: 'a1b2c3d'
        },
        blast_radius_summary: "This change impacts the core authentication flow. It introduces a risk to 3 downstream services.",
        impact_graph_data: { 
          nodes: [
            { data: { id: 'n1', label: 'AuthService', type: 'class', modified: true } },
            { data: { id: 'n2', label: 'UserController', type: 'class', modified: false } },
            { data: { id: 'n3', label: 'LoginHandler', type: 'method', modified: true } }
          ], 
          edges: [
            { data: { source: 'n2', target: 'n1', type: 'calls' } },
            { data: { source: 'n1', target: 'n3', type: 'contains' } }
          ] 
        },
        findings: [
          { id: 1, file_path: 'src/main.py', line_number: 45, severity: 'critical', category: 'security', description: 'Hardcoded API Key', suggested_fix: 'Use os.getenv()' },
          { id: 2, file_path: 'src/utils.py', line_number: 12, severity: 'medium', category: 'performance', description: 'O(N^2) loop detected', suggested_fix: 'Use a hash map' }
        ]
      });
    }
    return this.http.get<any>(`${this.apiUrl}/dashboard/jobs/${jobId}/findings`);
  }

  triggerReview(prUrl: string, scmAccountId?: number | null, llmModel?: string): Observable<any> {
    if (this.useMock) {
      return of({ status: 'queued', job_id: Math.floor(Math.random() * 1000) }).pipe(delay(500));
    }
    const payload: any = { pr_url: prUrl, scm_provider: 'github' };
    if (scmAccountId) {
      payload.scm_account_id = scmAccountId;
    }
    if (llmModel) {
      payload.llm_model = llmModel;
    }
    return this.http.post(`${this.apiUrl}/reviews/trigger`, payload);
  }

  getGithubRepositories(scmAccountId?: number): Observable<any[]> {
    if (this.useMock) return of([{ full_name: 'test/repo', name: 'repo' }]);
    let params: any = {};
    if (scmAccountId) params.scm_account_id = scmAccountId;
    return this.http.get<any[]>(`${this.apiUrl}/github/repos`, { params });
  }

  getGithubPullRequests(owner: string, repo: string, scmAccountId?: number): Observable<any[]> {
    if (this.useMock) return of([{ number: 42, title: 'Fix issue', html_url: 'https://github.com/test/repo/pull/42' }]);
    let params: any = {};
    if (scmAccountId) params.scm_account_id = scmAccountId;
    return this.http.get<any[]>(`${this.apiUrl}/github/repos/${owner}/${repo}/pulls`, { params });
  }

  getSettings(): Observable<any> {
    if (this.useMock) return of({ default_llm_model: 'ollama/qwen2.5-coder:7b', severity_threshold: 'low', custom_instructions: '' });
    return this.http.get<any>(`${this.apiUrl}/settings`);
  }

  updateSettings(data: any): Observable<any> {
    if (this.useMock) return of(data);
    return this.http.put<any>(`${this.apiUrl}/settings`, data);
  }
}
