import { Component, ChangeDetectionStrategy, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Router, RouterModule } from '@angular/router';
import { MatDialogModule, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { toSignal } from '@angular/core/rxjs-interop';
import { ApiService } from '../../core/services/api.service';
import { ScmService } from '../../core/services/scm.service';

@Component({
  selector: 'app-trigger-review-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatButtonModule, MatFormFieldModule, MatSelectModule, MatIconModule, MatDialogModule, MatProgressSpinnerModule, MatSnackBarModule],
  template: `
    <h2 mat-dialog-title>Trigger PR Review</h2>
    <mat-dialog-content>
      <form #triggerForm="ngForm" class="trigger-form">
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Select SCM Account</mat-label>
          <mat-select [(ngModel)]="selectedAccountId" name="scm_account" (selectionChange)="onAccountChange()" required>
            <mat-option *ngFor="let acc of accounts" [value]="acc.id">
              {{ acc.name }} ({{ acc.provider | titlecase }})
            </mat-option>
          </mat-select>
          <mat-hint *ngIf="accounts.length === 0">No accounts found.</mat-hint>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Select Repository</mat-label>
          <mat-select [(ngModel)]="selectedRepoFullName" name="repo" (selectionChange)="onRepoChange()" [disabled]="!selectedAccountId || isLoadingRepos" required>
            <mat-option *ngFor="let repo of repositories" [value]="repo.full_name">
              {{ repo.full_name }}
            </mat-option>
          </mat-select>
          <mat-spinner diameter="20" *ngIf="isLoadingRepos" matSuffix></mat-spinner>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Select Pull Request</mat-label>
          <mat-select [(ngModel)]="selectedPr" name="pr" [disabled]="!selectedRepoFullName || isLoadingPrs" required>
            <mat-option *ngFor="let pr of pullRequests" [value]="pr">
              #{{ pr.number }}: {{ pr.title }}
            </mat-option>
          </mat-select>
          <mat-spinner diameter="20" *ngIf="isLoadingPrs" matSuffix></mat-spinner>
        </mat-form-field>
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Select LLM Model</mat-label>
          <mat-select [(ngModel)]="selectedModel" name="llm_model">
            <mat-option value="">Default (Global)</mat-option>
            <mat-option value="ollama/qwen2.5-coder:7b">Qwen 2.5 Coder (Local)</mat-option>
            <mat-option value="openai/gpt-4o">GPT-4o (OpenAI)</mat-option>
            <mat-option value="gemini/gemini-1.5-pro">Gemini 1.5 Pro</mat-option>
          </mat-select>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button mat-raised-button color="primary" [disabled]="!triggerForm.valid || isSubmitting" (click)="onTrigger()">
        <span *ngIf="!isSubmitting">Trigger Review</span>
        <mat-spinner diameter="20" *ngIf="isSubmitting"></mat-spinner>
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .trigger-form { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 1rem; min-width: 400px; }
    .full-width { width: 100%; }
  `]
})
export class TriggerReviewDialogComponent implements OnInit {
  accounts: any[] = [];
  repositories: any[] = [];
  pullRequests: any[] = [];
  
  selectedAccountId: number | null = null;
  selectedRepoFullName: string = '';
  selectedPr: any = null;
  selectedModel: string = '';
  
  isLoadingRepos = false;
  isLoadingPrs = false;
  isSubmitting = false;

  constructor(
    private scmService: ScmService,
    private apiService: ApiService,
    private snackBar: MatSnackBar,
    private router: Router,
    public dialogRef: MatDialogRef<TriggerReviewDialogComponent>
  ) {}

  ngOnInit() {
    this.scmService.getAccounts().subscribe(accs => this.accounts = accs);
  }

  onAccountChange() {
    this.repositories = [];
    this.pullRequests = [];
    this.selectedRepoFullName = '';
    this.selectedPr = null;
    if (!this.selectedAccountId) return;
    
    this.isLoadingRepos = true;
    this.apiService.getGithubRepositories(this.selectedAccountId).subscribe({
      next: (repos) => {
        this.repositories = repos;
        this.isLoadingRepos = false;
      },
      error: () => {
         this.snackBar.open('Failed to load repositories', 'Close', { duration: 3000 });
         this.isLoadingRepos = false;
      }
    });
  }

  onRepoChange() {
    this.pullRequests = [];
    this.selectedPr = null;
    if (!this.selectedRepoFullName || !this.selectedAccountId) return;
    
    const [owner, repo] = this.selectedRepoFullName.split('/');
    
    this.isLoadingPrs = true;
    this.apiService.getGithubPullRequests(owner, repo, this.selectedAccountId).subscribe({
      next: (prs) => {
        this.pullRequests = prs;
        this.isLoadingPrs = false;
      },
      error: () => {
         this.snackBar.open('Failed to load PRs', 'Close', { duration: 3000 });
         this.isLoadingPrs = false;
      }
    });
  }

  onTrigger() {
    if (!this.selectedPr || !this.selectedAccountId) return;
    this.isSubmitting = true;
    
    this.apiService.triggerReview(this.selectedPr.html_url, this.selectedAccountId, this.selectedModel || undefined).subscribe({
      next: (res) => {
        this.snackBar.open('Review triggered successfully!', 'Close', { duration: 3000 });
        this.dialogRef.close(true);
      },
      error: (err) => {
        const msg = err.error?.detail || 'Failed to trigger review';
        this.snackBar.open(`Error: ${msg}`, 'Close', { duration: 5000 });
        this.isSubmitting = false;
      }
    });
  }
}

@Component({
  selector: 'app-jobs',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatChipsModule, MatButtonModule, MatIconModule, RouterModule, MatDialogModule],
  template: `
    <div class="header-container">
      <h1 class="mat-headline-3" style="margin: 0;">Recent Review Jobs</h1>
      <button mat-raised-button color="primary" (click)="openTriggerDialog()">
        <mat-icon>play_circle_filled</mat-icon> Trigger Review
      </button>
    </div>
    
    <div class="table-container mat-elevation-z1" *ngIf="jobs().length > 0; else noJobs">
      <table mat-table [dataSource]="jobs()" class="full-width-table">
        
        <!-- Run ID Column -->
        <ng-container matColumnDef="id">
          <th mat-header-cell *matHeaderCellDef> ID </th>
          <td mat-cell *matCellDef="let job"> #{{job.id}} </td>
        </ng-container>

        <!-- Repository Column -->
        <ng-container matColumnDef="repo_name">
          <th mat-header-cell *matHeaderCellDef> Repository </th>
          <td mat-cell *matCellDef="let job"> {{job.repo_name}} </td>
        </ng-container>

        <!-- PR Column -->
        <ng-container matColumnDef="pr">
          <th mat-header-cell *matHeaderCellDef> Pull Request </th>
          <td mat-cell *matCellDef="let job"> 
            <strong>#{{job.pr_number}}</strong>: {{job.pr_title}}
          </td>
        </ng-container>

        <!-- Status Column -->
        <ng-container matColumnDef="status">
          <th mat-header-cell *matHeaderCellDef> Status </th>
          <td mat-cell *matCellDef="let job">
            <mat-chip [color]="job.status === 'completed' || job.status === 'completed_publish_failed' ? 'primary' : (job.status === 'failed' ? 'warn' : 'accent')" highlighted>
              {{job.status | uppercase}}
            </mat-chip>
          </td>
        </ng-container>

        <!-- Started At Column -->
        <ng-container matColumnDef="started_at">
          <th mat-header-cell *matHeaderCellDef> Started At </th>
          <td mat-cell *matCellDef="let job"> {{job.started_at ? (job.started_at | date:'short') : 'N/A'}} </td>
        </ng-container>

        <!-- Completed At Column -->
        <ng-container matColumnDef="completed_at">
          <th mat-header-cell *matHeaderCellDef> Completed At </th>
          <td mat-cell *matCellDef="let job"> {{job.completed_at ? (job.completed_at | date:'short') : '-'}} </td>
        </ng-container>

        <!-- Latency Column -->
        <ng-container matColumnDef="latency">
          <th mat-header-cell *matHeaderCellDef> Time Taken </th>
          <td mat-cell *matCellDef="let job"> 
             <span *ngIf="job.latency_ms">{{ (job.latency_ms / 1000).toFixed(1) }}s</span>
             <span *ngIf="!job.latency_ms">-</span>
          </td>
        </ng-container>
        
        <!-- Tokens Column -->
        <ng-container matColumnDef="tokens">
          <th mat-header-cell *matHeaderCellDef> Tokens </th>
          <td mat-cell *matCellDef="let job"> 
             <mat-chip *ngIf="job.total_tokens" style="background: #f3e5f5; color: #7b1fa2;">
                {{ job.total_tokens | number }}
             </mat-chip>
             <span *ngIf="!job.total_tokens">-</span>
          </td>
        </ng-container>
        
        <!-- Action Column -->
        <ng-container matColumnDef="action">
          <th mat-header-cell *matHeaderCellDef></th>
          <td mat-cell *matCellDef="let job"> 
            <button mat-flat-button color="primary" [disabled]="job.status !== 'completed' && job.status !== 'completed_publish_failed'" [routerLink]="['/reviews', job.id]">
              View Report
            </button>
          </td>
        </ng-container>

        <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
        <tr mat-row *matRowDef="let row; columns: displayedColumns;" class="job-row"></tr>
      </table>
    </div>
    
    <ng-template #noJobs>
      <div class="table-container mat-elevation-z1" style="padding: 3rem; text-align: center; color: #666;">
        <mat-icon style="font-size: 48px; width: 48px; height: 48px; color: #ccc; margin-bottom: 1rem;">inbox</mat-icon>
        <h3>No review jobs yet</h3>
        <p>Trigger a review manually or configure a webhook to get started.</p>
      </div>
    </ng-template>
  `,
  styles: [`
    .header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .table-container { background: white; border-radius: 8px; overflow: hidden; margin-top: 1rem; }
    .full-width-table { width: 100%; }
    .job-row:hover { background: #f5f5f5; }
  `]
})
export class JobsComponent implements OnInit {
  private apiService = inject(ApiService);
  private dialog = inject(MatDialog);
  
  jobs = signal<any[]>([]);
  displayedColumns: string[] = ['id', 'repo_name', 'pr', 'status', 'started_at', 'completed_at', 'latency', 'tokens', 'action'];

  ngOnInit() {
    this.loadJobs();
  }
  
  loadJobs() {
    this.apiService.getRecentJobs().subscribe(data => {
      this.jobs.set(data || []);
    });
  }

  openTriggerDialog() {
    const dialogRef = this.dialog.open(TriggerReviewDialogComponent, {
      width: '600px',
      disableClose: true
    });
    
    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadJobs();
      }
    });
  }
}
