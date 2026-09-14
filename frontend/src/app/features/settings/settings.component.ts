import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule } from '@angular/forms';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule, MatSelectModule, FormsModule, MatSnackBarModule, MatProgressSpinnerModule],
  template: `
    <h1 class="mat-headline-3" style="margin-bottom: 2rem;">Platform Settings</h1>
    
    <div class="settings-grid" *ngIf="!isLoading()">
      
      <!-- Review Heuristics -->
      <mat-card class="settings-card mat-elevation-z1">
        <mat-card-header>
          <mat-icon mat-card-avatar color="primary">rule</mat-icon>
          <mat-card-title>Review Heuristics</mat-card-title>
          <mat-card-subtitle>Global rules for AI code reviews</mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <p class="help-text">Configure how strict the AI should be when flagging issues in pull requests.</p>
          
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Minimum Severity Threshold</mat-label>
            <mat-select [(ngModel)]="settings().severity_threshold">
              <mat-option value="low">Low (Report everything)</mat-option>
              <mat-option value="medium">Medium (Ignore minor nitpicks)</mat-option>
              <mat-option value="high">High (Only major bugs)</mat-option>
              <mat-option value="critical">Critical (Only security/blockers)</mat-option>
            </mat-select>
          </mat-form-field>
          
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Custom Instructions</mat-label>
            <textarea matInput [(ngModel)]="settings().custom_instructions" rows="4" placeholder="e.g. Strictly enforce OWASP Top 10 standards..."></textarea>
            <mat-hint>These instructions are appended directly to the LLM's system prompt.</mat-hint>
          </mat-form-field>
        </mat-card-content>
      </mat-card>

      <!-- LLM Providers -->
      <mat-card class="settings-card mat-elevation-z1">
        <mat-card-header>
          <mat-icon mat-card-avatar color="accent">smart_toy</mat-icon>
          <mat-card-title>LLM Providers</mat-card-title>
          <mat-card-subtitle>Global models and API Keys</mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <p class="help-text">Set your global default model and manage cloud API keys securely.</p>
          
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Global Default LLM Model</mat-label>
            <mat-select [(ngModel)]="settings().default_llm_model">
              <mat-option value="ollama/qwen2.5-coder:7b">Qwen 2.5 Coder (Local)</mat-option>
              <mat-option value="openai/gpt-4o">GPT-4o (OpenAI)</mat-option>
              <mat-option value="gemini/gemini-1.5-pro">Gemini 1.5 Pro</mat-option>
            </mat-select>
          </mat-form-field>
          
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>OpenAI API Key</mat-label>
            <input matInput type="password" [(ngModel)]="settings().openai_api_key" placeholder="sk-...">
            <button mat-icon-button matSuffix (click)="settings().openai_api_key = ''" *ngIf="settings().openai_api_key">
              <mat-icon>close</mat-icon>
            </button>
          </mat-form-field>
          
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Google Gemini API Key</mat-label>
            <input matInput type="password" [(ngModel)]="settings().google_api_key" placeholder="AIza...">
            <button mat-icon-button matSuffix (click)="settings().google_api_key = ''" *ngIf="settings().google_api_key">
              <mat-icon>close</mat-icon>
            </button>
          </mat-form-field>
        </mat-card-content>
      </mat-card>
      
    </div>
    
    <div class="actions" *ngIf="!isLoading()">
      <button mat-raised-button color="primary" class="save-btn" (click)="saveSettings()" [disabled]="isSaving()">
        <mat-spinner diameter="20" *ngIf="isSaving()"></mat-spinner>
        <span *ngIf="!isSaving()"><mat-icon>save</mat-icon> Save Configuration</span>
      </button>
    </div>
    
    <div class="loading-state" *ngIf="isLoading()">
      <mat-spinner diameter="40"></mat-spinner>
    </div>
  `,
  styles: [`
    .settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; }
    .settings-card { border-radius: 8px; }
    .help-text { color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }
    .full-width { width: 100%; margin-bottom: 0.5rem; }
    .actions { margin-top: 2rem; display: flex; justify-content: flex-end; }
    .save-btn { padding: 0 2rem; height: 48px; }
    .loading-state { display: flex; justify-content: center; margin-top: 4rem; }
    mat-card-avatar { background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
  `]
})
export class SettingsComponent implements OnInit {
  private apiService = inject(ApiService);
  private snackBar = inject(MatSnackBar);
  
  isLoading = signal(true);
  isSaving = signal(false);
  
  settings = signal<any>({
    default_llm_model: 'ollama/qwen2.5-coder:7b',
    severity_threshold: 'low',
    custom_instructions: '',
    openai_api_key: '',
    google_api_key: ''
  });

  ngOnInit() {
    this.apiService.getSettings().subscribe({
      next: (data) => {
        this.settings.set({ ...this.settings(), ...data });
        this.isLoading.set(false);
      },
      error: (err) => {
        this.snackBar.open('Failed to load settings', 'Close', { duration: 3000 });
        this.isLoading.set(false);
      }
    });
  }

  saveSettings() {
    this.isSaving.set(true);
    this.apiService.updateSettings(this.settings()).subscribe({
      next: (data) => {
        this.settings.set({ ...this.settings(), ...data });
        this.isSaving.set(false);
        this.snackBar.open('Settings saved successfully!', 'Close', { duration: 3000 });
      },
      error: (err) => {
        this.snackBar.open('Failed to save settings', 'Close', { duration: 3000 });
        this.isSaving.set(false);
      }
    });
  }
}
