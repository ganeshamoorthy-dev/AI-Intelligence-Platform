import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ScmService } from '../../core/services/scm.service';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-trigger',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatButtonModule, 
    MatInputModule, MatFormFieldModule, MatSelectModule, MatIconModule,
    MatSnackBarModule, MatProgressSpinnerModule
  ],
  template: `
    <div class="page-container">
      <div class="header">
        <h1>Manual Trigger Wizard</h1>
        <p>Trigger a PR review manually using your connected SCM accounts.</p>
      </div>

      <mat-card class="form-card mat-elevation-z2">
        <mat-card-content>
          <form (ngSubmit)="onTrigger()" #triggerForm="ngForm" class="trigger-form">
            
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Select SCM Account</mat-label>
              <mat-select [(ngModel)]="request.scm_account_id" name="scm_account" required>
                <mat-option *ngFor="let acc of accounts" [value]="acc.id">
                  {{ acc.name }} ({{ acc.provider | titlecase }})
                </mat-option>
              </mat-select>
              <mat-hint *ngIf="accounts.length === 0">No accounts found. Go to Integrations to connect one.</mat-hint>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Pull Request URL</mat-label>
              <input matInput [(ngModel)]="request.pr_url" name="pr_url" placeholder="https://github.com/owner/repo/pull/123" required>
            </mat-form-field>

            <button mat-raised-button color="primary" type="submit" [disabled]="!triggerForm.valid || isSubmitting" class="submit-btn">
              <mat-spinner diameter="20" *ngIf="isSubmitting"></mat-spinner>
              <span *ngIf="!isSubmitting">Trigger Review</span>
              <mat-icon *ngIf="!isSubmitting">play_arrow</mat-icon>
            </button>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .page-container { padding-bottom: 3rem; max-width: 800px; margin: 0 auto; }
    .header { margin-bottom: 2rem; }
    .header h1 { margin-bottom: 0.5rem; }
    .header p { color: #666; font-size: 1.1rem; }
    .form-card { padding: 2rem 1rem; }
    .trigger-form { display: flex; flex-direction: column; gap: 1.5rem; }
    .full-width { width: 100%; }
    .submit-btn { padding: 1.5rem 0; font-size: 1.1rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
  `]
})
export class TriggerComponent implements OnInit {
  accounts: any[] = [];
  request = { pr_url: '', scm_provider: 'github', scm_account_id: null as number | null };
  isSubmitting = false;

  constructor(
    private scmService: ScmService, 
    private apiService: ApiService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  ngOnInit() {
    this.scmService.getAccounts().subscribe({
      next: (data) => {
        this.accounts = data;
        if (data.length > 0) this.request.scm_account_id = data[0].id;
      },
      error: (err) => console.error(err)
    });
  }

  onTrigger() {
    this.isSubmitting = true;
    this.apiService.triggerReview(this.request.pr_url, this.request.scm_account_id).subscribe({
      next: (res: any) => {
        this.snackBar.open('Review triggered successfully!', 'View', { duration: 5000 }).onAction().subscribe(() => {
          this.router.navigate(['/reviews', res.job_id]);
        });
        this.router.navigate(['/jobs']);
        this.isSubmitting = false;
      },
      error: (err) => {
        this.snackBar.open(`Error: ${err.message}`, 'Close', { duration: 5000 });
        this.isSubmitting = false;
      }
    });
  }
}
