import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { ToolbarComponent } from '../toolbar/toolbar.component';
import { SidenavComponent } from '../sidenav/sidenav.component';

@Component({
  selector: 'app-page-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, MatSidenavModule, ToolbarComponent, SidenavComponent],
  template: `
    <div class="app-layout-container">
      <app-toolbar (toggleSidenav)="sidenav.toggle()"></app-toolbar>
      
      <mat-sidenav-container class="sidenav-container">
        <mat-sidenav #sidenav mode="side" opened class="app-sidenav">
          <app-sidenav></app-sidenav>
        </mat-sidenav>
        
        <mat-sidenav-content class="main-content">
          <router-outlet></router-outlet>
        </mat-sidenav-content>
      </mat-sidenav-container>
    </div>
  `,
  styles: [`
    .app-layout-container { display: flex; flex-direction: column; height: 100vh; }
    .sidenav-container { flex: 1; }
    .app-sidenav { width: 250px; }
    .main-content { padding: 1.5rem; background-color: #f5f5f5; min-height: 100%; box-sizing: border-box; }
    ::ng-deep .dark-theme .main-content { background-color: #303030; }
  `]
})
export class PageLayoutComponent {}
