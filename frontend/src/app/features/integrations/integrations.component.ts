import { Component, OnInit, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialogModule, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { ScmService } from '../../core/services/scm.service';

@Component({
  selector: 'app-create-scm-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatButtonModule, MatInputModule, MatFormFieldModule, MatSelectModule, MatIconModule, MatDialogModule],
  template: `
    <h2 mat-dialog-title>Connect New Account</h2>
    <mat-dialog-content>
      <form #accForm="ngForm" class="add-account-form">
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Account Name (e.g. Org Account)</mat-label>
          <input matInput [(ngModel)]="newAccount.name" name="name" required>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Provider</mat-label>
          <mat-select [(ngModel)]="newAccount.provider" name="provider" required>
            <mat-option value="github">GitHub</mat-option>
            <mat-option value="gitlab">GitLab (Coming Soon)</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Personal Access Token</mat-label>
          <input matInput type="password" [(ngModel)]="newAccount.access_token" name="access_token" required>
          <mat-hint>Requires 'repo' and 'admin:repo_hook' scopes for Webhook Registration.</mat-hint>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button mat-raised-button color="primary" [disabled]="!accForm.valid || isAdding" (click)="onAddAccount()">
        <mat-icon>add_link</mat-icon> Connect Account
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .add-account-form { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 1rem; min-width: 400px; }
    .full-width { width: 100%; }
  `]
})
export class CreateScmAccountDialogComponent {
  newAccount = { name: '', provider: 'github', access_token: '' };
  isAdding = false;

  constructor(
    private scmService: ScmService, 
    private snackBar: MatSnackBar,
    public dialogRef: MatDialogRef<CreateScmAccountDialogComponent>
  ) {}

  onAddAccount() {
    this.isAdding = true;
    this.scmService.createAccount(this.newAccount).subscribe({
      next: () => {
        this.snackBar.open('Account connected successfully!', 'Close', { duration: 3000 });
        this.isAdding = false;
        this.dialogRef.close(true);
      },
      error: (err) => {
        this.snackBar.open('Failed to connect account', 'Close', { duration: 3000 });
        this.isAdding = false;
      }
    });
  }
}

@Component({
  selector: 'app-integrations',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatButtonModule, 
    MatInputModule, MatFormFieldModule, MatSelectModule, MatIconModule,
    MatSnackBarModule, MatDividerModule, MatProgressSpinnerModule, MatDialogModule, MatTableModule, MatChipsModule, MatTabsModule
  ],
  template: `
    <div class="page-container">
      <div class="header">
        <div class="header-text">
          <h1>Integrations</h1>
          <p>Connect your SCM accounts and configure webhooks automatically.</p>
        </div>
      </div>

      <mat-tab-group animationDuration="0ms">
        <mat-tab label="SCM Accounts">
          <div class="tab-content-padding">
            <div style="display: flex; justify-content: flex-end; margin-bottom: 1.5rem;">
              <button mat-raised-button color="primary" (click)="openCreateDialog()">
                <mat-icon>add</mat-icon> Create Account
              </button>
            </div>
            <div class="accounts-list">
              <mat-card class="account-card mat-elevation-z1" *ngFor="let acc of accounts">
                <mat-card-header>
                  <div mat-card-avatar class="provider-icon">
                    <mat-icon>{{ acc.provider === 'github' ? 'code' : 'dns' }}</mat-icon>
                  </div>
                  <mat-card-title>{{ acc.name }}</mat-card-title>
                  <mat-card-subtitle>{{ acc.provider | titlecase }} Account</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content>
                  <p class="meta">Connected on {{ acc.created_at | date:'mediumDate' }}</p>
                  
                  <mat-divider style="margin: 1rem 0;"></mat-divider>
                  
                  <h4>Quick Actions</h4>
                  <div class="quick-actions">
                    <mat-form-field appearance="outline" class="webhook-input">
                      <mat-label>Repository URL</mat-label>
                      <input matInput [(ngModel)]="repoUrlToRegister[acc.id]" placeholder="https://github.com/owner/repo">
                    </mat-form-field>
                    <mat-form-field appearance="outline" class="model-select">
                      <mat-label>LLM Model</mat-label>
                      <mat-select [(ngModel)]="selectedModel[acc.id]">
                        <mat-option value="">Default (Global)</mat-option>
                        <mat-option value="ollama/qwen2.5-coder:7b">Qwen 2.5 Coder (Local)</mat-option>
                        <mat-option value="openai/gpt-4o">GPT-4o (OpenAI)</mat-option>
                        <mat-option value="gemini/gemini-1.5-pro">Gemini 1.5 Pro</mat-option>
                      </mat-select>
                    </mat-form-field>
                    <button mat-stroked-button color="accent" (click)="registerWebhook(acc.id)" [disabled]="!repoUrlToRegister[acc.id] || isRegistering[acc.id]">
                      <mat-spinner diameter="20" *ngIf="isRegistering[acc.id]"></mat-spinner>
                      <span *ngIf="!isRegistering[acc.id]">Register Webhook</span>
                    </button>
                  </div>
                </mat-card-content>
              </mat-card>
              
              <div *ngIf="accounts.length === 0" class="empty-state">
                <mat-icon class="empty-icon">link_off</mat-icon>
                <h3>No accounts connected</h3>
                <p>Connect an SCM account to start managing webhooks.</p>
                <button mat-stroked-button color="primary" style="margin-top: 1rem;" (click)="openCreateDialog()">
                  Connect your first account
                </button>
              </div>
            </div>
          </div>
        </mat-tab>
        
        <mat-tab label="Configured Webhooks">
          <div class="tab-content-padding">
            <p style="color: #666; margin-bottom: 1.5rem;">Repositories currently configured to trigger reviews automatically on new Pull Requests.</p>
            <div class="table-container mat-elevation-z1">
              <table mat-table [dataSource]="webhooks" class="full-width-table">
                <ng-container matColumnDef="repo">
                  <th mat-header-cell *matHeaderCellDef> Repository </th>
                  <td mat-cell *matCellDef="let hook">
                    <strong>{{hook.project_name}}</strong>
                  </td>
                </ng-container>
                <ng-container matColumnDef="url">
                  <th mat-header-cell *matHeaderCellDef> URL </th>
                  <td mat-cell *matCellDef="let hook"> <a [href]="hook.repository_url" target="_blank">{{hook.repository_url}}</a> </td>
                </ng-container>
                <ng-container matColumnDef="account">
                  <th mat-header-cell *matHeaderCellDef> SCM Account </th>
                  <td mat-cell *matCellDef="let hook"> <mat-chip>{{hook.account_name}}</mat-chip> </td>
                </ng-container>
                <ng-container matColumnDef="events">
                  <th mat-header-cell *matHeaderCellDef> Events </th>
                  <td mat-cell *matCellDef="let hook"> 
                     <span *ngFor="let ev of hook.events; let last = last">{{ev}}{{last ? '' : ', '}}</span>
                  </td>
                </ng-container>
                <ng-container matColumnDef="created">
                  <th mat-header-cell *matHeaderCellDef> Registered At </th>
                  <td mat-cell *matCellDef="let hook"> {{hook.created_at | date:'shortDate'}} </td>
                </ng-container>
                
                <tr mat-header-row *matHeaderRowDef="['repo', 'url', 'account', 'events', 'created']"></tr>
                <tr mat-row *matRowDef="let row; columns: ['repo', 'url', 'account', 'events', 'created'];"></tr>
              </table>
              
              <div *ngIf="webhooks.length === 0" style="padding: 2rem; text-align: center; color: #666;">
                 No webhooks configured yet. Register one using the Quick Actions in the SCM Accounts tab!
              </div>
            </div>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .page-container { padding-bottom: 3rem; }
    .tab-content-padding { padding: 1.5rem 0; }
    .header { margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }
    .header h1 { margin-bottom: 0.5rem; }
    .header p { color: #666; font-size: 1.1rem; margin: 0; }
    .header-actions { margin-top: 0.5rem; }
    
    .accounts-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1.5rem; }
    .account-card { border-left: 4px solid #3f51b5; display: flex; flex-direction: column; }
    .provider-icon { background: #e8eaf6; color: #3f51b5; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
    .meta { color: #666; font-size: 0.9rem; margin-top: 1rem; }
    
    .quick-actions { display: flex; align-items: flex-start; gap: 1rem; margin-top: 0.5rem; flex-wrap: wrap; }
    .webhook-input { flex: 1; min-width: 200px; margin-bottom: -1.25em; }
    .quick-actions button { height: 56px; margin-top: 0px; }
    
    .empty-state { grid-column: 1 / -1; text-align: center; padding: 4rem 2rem; background: #fff; border-radius: 8px; border: 1px dashed #ccc; }
    .empty-icon { font-size: 48px; width: 48px; height: 48px; color: #ccc; margin-bottom: 1rem; }
    .empty-state h3 { margin: 0; color: #555; }
    .empty-state p { color: #888; }
  `]
})
export class IntegrationsComponent implements OnInit {
  accounts: any[] = [];
  webhooks: any[] = [];
  repoUrlToRegister: { [key: number]: string } = {};
  selectedModel: { [key: number]: string } = {};
  isRegistering: { [key: number]: boolean } = {};

  constructor(
    private scmService: ScmService, 
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  ngOnInit() {
    this.loadAccounts();
    this.loadWebhooks();
  }

  loadAccounts() {
    this.scmService.getAccounts().subscribe({
      next: (data) => this.accounts = data,
      error: (err) => console.error(err)
    });
  }

  loadWebhooks() {
    this.scmService.getWebhooks().subscribe({
      next: (data) => this.webhooks = data,
      error: (err) => console.error(err)
    });
  }

  openCreateDialog() {
    const dialogRef = this.dialog.open(CreateScmAccountDialogComponent, {
      width: '500px',
      disableClose: true
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadAccounts();
      }
    });
  }

  registerWebhook(accountId: number) {
    const url = this.repoUrlToRegister[accountId];
    const model = this.selectedModel[accountId];
    if (!url) return;
    
    this.isRegistering[accountId] = true;
    const payload: any = { scm_account_id: accountId, repository_url: url };
    if (model) {
      payload.llm_model = model;
    }
    
    this.scmService.registerWebhook(payload).subscribe({
      next: (res) => {
        this.snackBar.open('Webhook registered automatically!', 'Close', { duration: 5000 });
        this.repoUrlToRegister[accountId] = '';
        this.selectedModel[accountId] = '';
        this.isRegistering[accountId] = false;
        this.loadWebhooks();
      },
      error: (err) => {
        const msg = err.error?.detail || 'Failed to register webhook';
        this.snackBar.open(`Error: ${msg}`, 'Close', { duration: 5000 });
        this.isRegistering[accountId] = false;
      }
    });
  }
}
