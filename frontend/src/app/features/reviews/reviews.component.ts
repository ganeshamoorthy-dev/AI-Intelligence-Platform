import { Component, ChangeDetectionStrategy, inject, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { FormsModule } from '@angular/forms';
import { toSignal } from '@angular/core/rxjs-interop';
import { computed } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { ActivatedRoute } from '@angular/router';
import { switchMap, takeWhile } from 'rxjs/operators';
import { of, timer } from 'rxjs';
import { Network } from 'vis-network';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';

@Component({
  selector: 'app-reviews',
  standalone: true,
  imports: [CommonModule, FormsModule, MatTableModule, MatChipsModule, MatCardModule, MatIconModule, MatButtonModule, MatSidenavModule, MatDividerModule, MatButtonToggleModule, MatTabsModule, MatExpansionModule],
  changeDetection: ChangeDetectionStrategy.Default,
  template: `
    <ng-container *ngIf="reviewData() as data; else loading">
      <div *ngIf="data.pr_metadata.status === 'completed' || data.pr_metadata.status === 'completed_publish_failed' || data.pr_metadata.status === 'failed'; else processing" class="review-container">
      
      <!-- Phase 1 PR Header (Compacted) -->
      <div class="pr-header mat-elevation-z1" *ngIf="data.pr_metadata as pr" style="background: white; border-radius: 8px; overflow: hidden; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem;">
        <div>
          <div style="color: #666; font-size: 0.9rem; font-weight: 500; margin-bottom: 0.25rem;">Review #{{ pr.number }}</div>
          <h1 style="margin: 0; font-size: 1.25rem;">{{ pr.repo_name }} / {{ pr.title }}</h1>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
          <div style="font-size: 0.9rem; font-weight: 500; display: flex; align-items: center; gap: 0.5rem;">
            Risk: 
            <span [ngStyle]="{
              'color': pr.risk_level === 'high' || pr.risk_level === 'critical' ? '#f44336' : (pr.risk_level === 'medium' ? '#ff9800' : '#4caf50'),
              'text-transform': 'capitalize',
              'font-weight': 'bold'
            }">{{ pr.risk_level || 'Unknown' }}</span>
          </div>
          <mat-chip [color]="pr.status === 'completed' ? 'primary' : 'warn'" highlighted style="min-height: 24px; font-size: 0.85rem;">{{ pr.status | uppercase }}</mat-chip>
        </div>
      </div>

      <mat-tab-group animationDuration="0ms" class="review-tabs" (selectedTabChange)="onTabChange($event)">
        
        <!-- Tab 1: Overview -->
        <mat-tab label="Overview">
          <ng-template matTabContent>
            <div class="tab-content-padding" style="background: #fafafa; padding: 2rem;">
               <!-- Metrics moved from Header -->
               <div class="summary-cards-container" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 1.5rem;">
                  <mat-card class="summary-card mat-elevation-z1" style="padding: 1rem;">
                     <div class="summary-value" style="color: #666;">{{ data.pr_metadata?.changed_files_count || 0 }}</div>
                     <div class="summary-label">Changed Files</div>
                  </mat-card>
                  <mat-card class="summary-card mat-elevation-z1" style="padding: 1rem;">
                     <div class="summary-value" style="color: #666;">{{ data.pr_metadata?.affected_files_count || 0 }}</div>
                     <div class="summary-label">Affected Files</div>
                  </mat-card>
                  <mat-card class="summary-card mat-elevation-z1" style="padding: 1rem;">
                     <div class="summary-value" [style.color]="data.pr_metadata?.findings_count > 0 ? '#f44336' : '#4caf50'">{{ data.pr_metadata?.findings_count || 0 }}</div>
                     <div class="summary-label">Findings</div>
                  </mat-card>
               </div>

               <!-- Original Overview Metrics -->
               <div class="summary-cards-container">
                 <mat-card class="summary-card">
                   <div class="summary-value">{{ treeData.length > 0 ? treeData.length : '?' }}</div>
                   <div class="summary-label">Modified Nodes</div>
                 </mat-card>
                 <mat-card class="summary-card">
                   <div class="summary-value">{{ tableEdgesData.length }}</div>
                   <div class="summary-label">Impacted Connections</div>
                 </mat-card>
                 <mat-card class="summary-card">
                   <div class="summary-value" style="color: #f44336">{{ data.findings?.length || 0 }}</div>
                   <div class="summary-label">AI Findings</div>
                 </mat-card>
                 <mat-card class="summary-card">
                   <div class="summary-value" style="color: #4caf50">{{ data.pr_metadata.latency_ms ? (data.pr_metadata.latency_ms / 1000).toFixed(1) + 's' : '-' }}</div>
                   <div class="summary-label">Time Taken</div>
                 </mat-card>
                 <mat-card class="summary-card">
                   <div class="summary-value" style="color: #9c27b0">{{ data.pr_metadata.input_tokens ? (data.pr_metadata.input_tokens | number) : '-' }}</div>
                   <div class="summary-label">Input Tokens</div>
                 </mat-card>
                 <mat-card class="summary-card">
                   <div class="summary-value" style="color: #673ab7">{{ data.pr_metadata.output_tokens ? (data.pr_metadata.output_tokens | number) : '-' }}</div>
                   <div class="summary-label">Output Tokens</div>
                 </mat-card>
               </div>

            <!-- Blast Radius Summary -->
            <mat-card class="blast-radius-card mat-elevation-z2" *ngIf="data.blast_radius_summary" style="margin-top: 2rem;">
              <mat-card-header>
                <mat-card-title>Blast Radius Summary</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <p class="summary-text">{{ data.blast_radius_summary }}</p>
              </mat-card-content>
            </mat-card>
            </div>
          </ng-template>
        </mat-tab>



        <!-- Tab 2: Findings -->
        <mat-tab label="Findings">
          <ng-template matTabContent>
            <div class="tab-content-padding" style="background: #fafafa; padding: 2rem;">
               <div *ngIf="data.findings.length === 0" style="text-align: center; color: #666; padding: 3rem;">
                  <mat-icon style="font-size: 48px; width: 48px; height: 48px; color: #ccc;">check_circle_outline</mat-icon>
                  <h2>No Issues Found</h2>
                  <p>The AI reviewer didn't flag any issues for this pull request.</p>
               </div>

               <div style="display: flex; flex-direction: column; gap: 1.5rem; max-width: 900px; margin: 0 auto;">
                  <mat-accordion multi>
                    <mat-expansion-panel *ngFor="let group of groupedFindings()" [expanded]="true" class="mat-elevation-z1" style="margin-bottom: 1rem; border-radius: 8px; overflow: hidden;">
                      <mat-expansion-panel-header style="background: #f8f9fa; border-bottom: 1px solid #e0e0e0;">
                        <mat-panel-title style="font-family: monospace; font-size: 0.95rem; font-weight: 600; color: #333; display: flex; align-items: center; gap: 0.5rem;">
                          <mat-icon style="color: #666; font-size: 20px; width: 20px; height: 20px;">description</mat-icon>
                          {{ group.file_path }}
                        </mat-panel-title>
                        <mat-panel-description style="display: flex; justify-content: flex-end; align-items: center;">
                          <mat-chip style="min-height: 20px; font-size: 0.75rem;">{{ group.findings.length }} finding(s)</mat-chip>
                        </mat-panel-description>
                      </mat-expansion-panel-header>

                      <div style="padding: 1rem 0; display: flex; flex-direction: column; gap: 1rem;">
                        <mat-card *ngFor="let element of group.findings" class="finding-card mat-elevation-z1" style="border-radius: 8px; overflow: hidden; border-left: 4px solid" [ngStyle]="{'border-left-color': getSeverityColor(element.severity)}">
                           <mat-card-header style="padding: 1rem 1rem 0.5rem; display: flex; justify-content: space-between; align-items: flex-start;">
                              <div style="display: flex; align-items: center; gap: 0.75rem;">
                                 <div [ngStyle]="{'background': getSeverityColor(element.severity) + '22', 'color': getSeverityColor(element.severity)}" style="padding: 2px 8px; border-radius: 12px; font-weight: bold; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.5px;">
                                    {{element.severity}}
                                 </div>
                                 <mat-chip-set>
                                    <mat-chip style="font-size: 0.7rem; height: 20px; min-height: 20px;">{{element.category}}</mat-chip>
                                 </mat-chip-set>
                                 <div *ngIf="element.confidence" style="font-size: 0.75rem; color: #666; display: flex; align-items: center; gap: 4px;">
                                    <mat-icon style="font-size: 14px; width: 14px; height: 14px;">psychology</mat-icon> {{element.confidence}} Confidence
                                 </div>
                              </div>
                              <div *ngIf="element.line_number" style="font-family: monospace; font-size: 0.8rem; background: #f0f0f0; padding: 2px 8px; border-radius: 4px; color: #333;">
                                 Line {{element.line_number}}
                              </div>
                           </mat-card-header>

                           <mat-card-content style="padding: 0 1rem 1rem;">
                              <p style="font-size: 1rem; color: #222; margin: 0.75rem 0; line-height: 1.4;">{{element.description}}</p>

                              <div *ngIf="element.why_it_matters" style="background: #f8f9fa; border-left: 3px solid #9c27b0; padding: 0.75rem; margin: 0.75rem 0; border-radius: 0 6px 6px 0;">
                                 <strong style="color: #9c27b0; font-size: 0.8rem; text-transform: uppercase;">Why it matters</strong>
                                 <p style="margin: 0.25rem 0 0; color: #444; font-size: 0.9rem;">{{element.why_it_matters}}</p>
                              </div>

                              <div *ngIf="element.evidence" style="margin-top: 1rem;">
                                 <strong style="color: #555; font-size: 0.8rem; text-transform: uppercase;">Code Evidence</strong>
                                 <pre style="background: #2d2d2d; color: #e0e0e0; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; margin-top: 0.25rem; border: 1px solid #444;"><code>{{element.evidence}}</code></pre>
                              </div>

                              <div *ngIf="element.suggested_fix" style="margin-top: 1rem;">
                                 <strong style="color: #2e7d32; font-size: 0.8rem; text-transform: uppercase;">Suggested Fix</strong>
                                 <pre style="background: #f1f8e9; color: #1b5e20; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; margin-top: 0.25rem; border: 1px solid #c5e1a5;"><code>{{element.suggested_fix}}</code></pre>
                              </div>
                           </mat-card-content>
                        </mat-card>
                      </div>
                    </mat-expansion-panel>
                  </mat-accordion>
               </div>
            </div>
          </ng-template>
        </mat-tab>

        <!-- Tab 3: Dependencies -->
        <mat-tab label="Dependencies">
          <ng-template matTabContent>
            <mat-drawer-container class="graph-drawer-container mat-elevation-z2" *ngIf="data.impact_graph_data" style="margin-top: 1rem;">
              <mat-drawer-content>
                <div class="graph-header" style="background: white; border-bottom: 1px solid #e0e0e0;">
                  <!-- Impact Summary Cards (Milestone 2) -->
                  <div class="impact-summary-container" *ngIf="impactSummary() as summary" style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
                    <div class="impact-metric">
                      <div class="metric-value">{{ summary.changedSymbols }}</div>
                      <div class="metric-label">Changed Symbols</div>
                    </div>
                    <div class="impact-metric">
                      <div class="metric-value">{{ summary.appDependencies }}</div>
                      <div class="metric-label">App Dependencies</div>
                    </div>
                    <div class="impact-metric">
                      <div class="metric-value">{{ summary.externalDependencies }}</div>
                      <div class="metric-label">External Dependencies</div>
                    </div>
                    <div class="impact-metric" [ngClass]="'risk-' + summary.impactLevel.toLowerCase()">
                      <div class="metric-value" style="font-size: 18px; line-height: 32px;">{{ summary.impactLevel }}</div>
                      <div class="metric-label">Potential Impact</div>
                    </div>
                  </div>

                  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #eee;">
                    <h3 style="margin: 0; font-size: 1.5rem; font-weight: 500; color: #333;">Dependency Analysis</h3>
                    <div style="display: flex; align-items: center; gap: 1.5rem;">
                        <!-- Review Scope Controls (Milestone 4) -->
                        <div style="display: flex; align-items: center; gap: 1rem; padding: 0.25rem 1rem; background: #f8f9fa; border-radius: 20px; border: 1px solid #e0e0e0;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                               <span style="font-size: 11px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Depth</span>
                               <mat-button-toggle-group [(ngModel)]="scopeDepth" (change)="onScopeChange()" style="height: 28px; align-items: center;">
                                  <mat-button-toggle value="0" style="padding: 0 8px; line-height: 28px; font-size: 12px;">0-Hop</mat-button-toggle>
                                  <mat-button-toggle value="1" style="padding: 0 8px; line-height: 28px; font-size: 12px;">1-Hop</mat-button-toggle>
                               </mat-button-toggle-group>
                            </div>
                            
                            <mat-divider vertical style="height: 20px;"></mat-divider>
                            
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                               <span style="font-size: 11px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Direction</span>
                               <mat-button-toggle-group [(ngModel)]="scopeDirection" (change)="onScopeChange()" style="height: 28px; align-items: center;">
                                  <mat-button-toggle value="incoming" style="padding: 0 8px; line-height: 28px; font-size: 12px;">Incoming</mat-button-toggle>
                                  <mat-button-toggle value="outgoing" style="padding: 0 8px; line-height: 28px; font-size: 12px;">Outgoing</mat-button-toggle>
                                  <mat-button-toggle value="both" style="padding: 0 8px; line-height: 28px; font-size: 12px;">Both</mat-button-toggle>
                               </mat-button-toggle-group>
                            </div>
                            
                            <mat-divider vertical style="height: 20px;"></mat-divider>
                            
                            <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 12px; font-weight: 500; cursor: pointer; margin: 0;">
                               <input type="checkbox" [(ngModel)]="includeExternal" (change)="onScopeChange()"> Include External
                            </label>
                        </div>
                        
                        <mat-button-toggle-group [(ngModel)]="viewMode" (change)="onViewModeChange()" aria-label="View Mode">
                          <mat-button-toggle value="tree"><mat-icon style="font-size: 18px; width: 18px; height: 18px; line-height: 18px;">account_tree</mat-icon> Tree</mat-button-toggle>
                          <mat-button-toggle value="graph"><mat-icon style="font-size: 18px; width: 18px; height: 18px; line-height: 18px;">share</mat-icon> Graph</mat-button-toggle>
                          <mat-button-toggle value="table"><mat-icon style="font-size: 18px; width: 18px; height: 18px; line-height: 18px;">table_chart</mat-icon> Table</mat-button-toggle>
                        </mat-button-toggle-group>
                    </div>
                  </div>
                  
                  <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;" *ngIf="viewMode === 'graph'">
                    <span style="font-weight: 500;">Color:</span>
                    <mat-chip-listbox [multiple]="false" (change)="toggleColorMode($event)">
                      <mat-chip-option [selected]="colorMode === 'type'" value="type">By Type</mat-chip-option>
                      <mat-chip-option [selected]="colorMode === 'risk'" value="risk">By Risk</mat-chip-option>
                    </mat-chip-listbox>
                    
                    <mat-divider vertical style="height: 30px;"></mat-divider>
                    
                    <span style="font-weight: 500;">Edges:</span>
                    <mat-chip-listbox multiple>
                      <mat-chip-option *ngFor="let et of availableEdgeTypes" selected color="primary" (selectionChange)="toggleEdgeType(et)">{{ et }}</mat-chip-option>
                    </mat-chip-listbox>
                  </div>

                  <div class="legend" *ngIf="viewMode === 'graph' && colorMode === 'type'">
                    <span class="legend-item"><span class="swatch" style="background: #9c27b0"></span> File</span>
                    <span class="legend-item"><span class="swatch" style="background: #ffc107"></span> Class</span>
                    <span class="legend-item"><span class="swatch" style="background: #00bcd4"></span> Function</span>
                    <span class="legend-item"><span class="swatch" style="background: #4caf50"></span> Test</span>
                    <span class="legend-item"><span class="swatch" style="background: #e0e0e0"></span> External</span>
                  </div>
                  
                  <div class="legend" *ngIf="viewMode === 'graph' && colorMode === 'risk'">
                    <span class="legend-item"><span class="swatch changed"></span> Modified</span>
                    <span class="legend-item"><span class="swatch impacted"></span> Impacted (1-Hop)</span>
                    <span class="legend-item"><span class="swatch risk-high"></span> Findings</span>
                  </div>
                </div>
                
                <div #cyContainer class="cy-container" [style.display]="viewMode === 'graph' ? 'block' : 'none'"></div>
                
                <!-- Tree View -->
                <div class="tree-container" *ngIf="viewMode === 'tree'">
                  <div *ngIf="treeData.length === 0" style="padding: 2rem; text-align: center; color: #666;">No dependency data to show.</div>
                  <div *ngFor="let node of treeData" class="tree-parent-node">
                    <div class="tree-parent-header" style="display: flex; align-items: flex-start; margin-bottom: 0.5rem; cursor: pointer; padding: 0.5rem; border-radius: 4px; transition: background 0.2s;" (click)="onNodeSelect(node.originalNode)" onmouseover="this.style.background='#f5f5f5'" onmouseout="this.style.background='transparent'">
                        <mat-icon [style.color]="getNodeColor(node.type)" style="margin-right: 0.5rem;">{{getIconForType(node.type)}}</mat-icon>
                        <div style="display: flex; flex-direction: column;">
                           <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                             <strong style="font-size: 1.1em;">{{ getShortLabel(node.label) }}</strong> 
                             <span class="type-badge">{{ getNodeType(node.originalNode) }}</span>
                             <span class="type-badge" style="background: #ffebee; color: #c62828;" *ngIf="node.modified">MODIFIED</span>
                             <span class="type-badge" style="background: #e0e0e0; color: #424242;" *ngIf="isExternal(node.originalNode)">EXTERNAL</span>
                           </div>
                           <div style="font-size: 0.85em; color: #666; margin-top: 0.25rem;" *ngIf="node.originalNode?.file || node.originalNode?.source_file">
                             {{ node.originalNode?.source_file || node.originalNode?.file }}:{{ node.originalNode?.source_location || 'L?' }}
                           </div>
                           <div style="font-size: 0.85em; color: #999;" *ngIf="getShortLabel(node.label) !== node.label">{{ node.label }}</div>
                        </div>
                    </div>
                    <div class="tree-children" style="margin-left: 2rem; border-left: 1px solid #eee; padding-left: 1rem;">
                      <div *ngFor="let child of node.children" class="tree-child-row" style="display: flex; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; cursor: pointer; padding: 0.25rem; border-radius: 4px; transition: background 0.2s;" (click)="onNodeSelect(child.originalNode)" onmouseover="this.style.background='#f5f5f5'" onmouseout="this.style.background='transparent'">
                          <div class="relation-badge" style="margin-right: 0.5rem;">{{ child.relation }}</div>
                          <mat-icon style="font-size: 16px; width: 16px; height: 16px; margin: 0 0.5rem;" [style.color]="getNodeColor(child.type)">{{getIconForType(child.type)}}</mat-icon>
                          <div style="display: flex; flex-direction: column;">
                              <div style="display: flex; align-items: center; gap: 0.5rem;">
                                  <span>{{ getShortLabel(child.label) }}</span>
                                  <span class="type-badge" style="background: #e0e0e0; color: #424242; font-size: 0.7em;" *ngIf="isExternal(child.originalNode)">EXTERNAL</span>
                              </div>
                              <div style="font-size: 0.8em; color: #999;" *ngIf="getShortLabel(child.label) !== child.label">{{ child.label }}</div>
                          </div>
                      </div>
                      <div *ngIf="node.children.length === 0" style="color: #999; font-style: italic; padding-top: 0.5rem; padding-bottom: 0.5rem;">
                        No dependencies impacted <span *ngIf="!includeExternal" style="font-size: 0.85em;">(Try including External Libraries)</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Table View -->
                <div class="impact-table-container" *ngIf="viewMode === 'table'">
                  <table mat-table [dataSource]="tableEdgesData" class="full-width-table">
                      <ng-container matColumnDef="source">
                        <th mat-header-cell *matHeaderCellDef> Source Component </th>
                        <td mat-cell *matCellDef="let edge"> {{edge.sourceName}} </td>
                      </ng-container>
                      <ng-container matColumnDef="relation">
                        <th mat-header-cell *matHeaderCellDef> Relationship </th>
                        <td mat-cell *matCellDef="let edge"> <mat-chip highlighted>{{edge.relation}}</mat-chip> </td>
                      </ng-container>
                      <ng-container matColumnDef="target">
                        <th mat-header-cell *matHeaderCellDef> Impacted Target </th>
                        <td mat-cell *matCellDef="let edge"> {{edge.targetName}} </td>
                      </ng-container>
                      <tr mat-header-row *matHeaderRowDef="['source', 'relation', 'target']"></tr>
                      <tr mat-row *matRowDef="let row; columns: ['source', 'relation', 'target'];"></tr>
                  </table>
                </div>
              </mat-drawer-content>
              <mat-drawer #drawer mode="over" position="end" class="details-drawer">
                <div class="drawer-header">
                  <h3>Node Details</h3>
                  <button mat-icon-button (click)="drawer.close()"><mat-icon>close</mat-icon></button>
                </div>
                <div class="drawer-content" *ngIf="selectedNode">
                  <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                    <mat-icon [style.color]="getNodeColor(selectedNode.data('type'))">{{getIconForType(selectedNode.data('type'))}}</mat-icon>
                    <h2 style="margin: 0; font-size: 1.2em; word-break: break-all;">{{ getShortLabel(selectedNode.data('label') || selectedNode.data('id')) }}</h2>
                  </div>
                  
                  <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
                    <span class="type-badge">{{ getNodeType(selectedNode.data('')) || selectedNode.data('type') || 'Unknown' }}</span>
                    <span class="type-badge" style="background: #ffebee; color: #c62828;" *ngIf="selectedNode.data('modified')">MODIFIED</span>
                    <span class="type-badge" style="background: #e0e0e0; color: #424242;" *ngIf="isExternal(selectedNode.data(''))">EXTERNAL</span>
                  </div>
                  
                  <p *ngIf="selectedNode.data('source_file')" style="font-size: 0.9em; color: #666; font-family: monospace; word-break: break-all;">
                    {{ selectedNode.data('source_file') }}:{{ selectedNode.data('source_location') || 'L?' }}
                  </p>
                  
                  <!-- Milestone 5: Explanation -->
                  <div *ngIf="selectedNodeExplanation" style="background: #f5f5f5; border-left: 4px solid #2196f3; padding: 1rem; margin: 1.5rem 0; border-radius: 0 4px 4px 0;">
                     <h4 style="margin-top: 0; margin-bottom: 0.5rem; color: #1976d2;">Why is this included?</h4>
                     <p style="margin: 0; font-size: 0.95em; color: #424242;">{{ selectedNodeExplanation }}</p>
                  </div>
                  
                  <a mat-stroked-button color="primary" class="full-width-btn" [href]="getGithubUrl(selectedNode.data('source_file') || selectedNode.data('id'), data.pr_metadata)" target="_blank">
                    <mat-icon>launch</mat-icon> View File on GitHub
                  </a>
                  
                  <!-- Milestone 5: Source Snippet -->
                  <div *ngIf="selectedNodeSnippet">
                    <mat-divider style="margin: 1.5rem 0;"></mat-divider>
                    <h4>Source Evidence</h4>
                    <pre style="background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 4px; overflow-x: auto; font-size: 13px; line-height: 1.4; margin: 0;"><code>{{ selectedNodeSnippet }}</code></pre>
                  </div>
                  
                  <div *ngIf="selectedNodeFindings.length > 0">
                    <mat-divider style="margin: 1.5rem 0;"></mat-divider>
                    <h4>Associated AI Findings</h4>
                    <div *ngFor="let f of selectedNodeFindings" class="node-finding">
                      <mat-chip color="warn" highlighted>{{f.severity}}</mat-chip>
                      <p>{{f.description}}</p>
                    </div>
                  </div>
                </div>
              </mat-drawer>
            </mat-drawer-container>
          </ng-template>
        </mat-tab>

        <!-- Tab 4: AI Context Explorer -->
        <mat-tab label="AI Context">
           <div class="tab-content-padding" style="background: #fafafa; padding: 2rem;">
              <div *ngIf="!data.impact_graph_data?.review_context" style="text-align: center; color: #666; padding: 3rem;">
                 <mat-icon style="font-size: 48px; width: 48px; height: 48px; color: #ccc;">visibility_off</mat-icon>
                 <h2>Context Not Available</h2>
                 <p>This review was processed before the Context Engine was enabled.</p>
              </div>

              <div *ngIf="data.impact_graph_data?.review_context as ctx">
                 <div style="margin-bottom: 2rem; background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0;">
                    <h3 style="margin-top: 0; color: #333; font-weight: 500;">What did the AI see?</h3>
                    <p style="color: #555; margin-bottom: 0;">{{ ctx.context_summary }}</p>
                 </div>

                 <!-- Directly Changed Code -->
                 <div *ngIf="ctx.source_snippets?.length > 0" class="context-section">
                    <h4 class="context-section-title"><mat-icon>code</mat-icon> Included Source Code</h4>
                    <mat-accordion>
                       <mat-expansion-panel *ngFor="let snippet of ctx.source_snippets" class="mat-elevation-z1">
                          <mat-expansion-panel-header>
                             <mat-panel-title style="font-family: monospace; font-weight: 500;">
                                {{ getShortLabel(snippet.node_id) }}
                             </mat-panel-title>
                          </mat-expansion-panel-header>
                          <pre class="snippet-block"><code>{{ snippet.content }}</code></pre>
                       </mat-expansion-panel>
                    </mat-accordion>
                 </div>

                 <!-- Direct Callers -->
                 <div *ngIf="ctx.direct_callers?.length > 0" class="context-section">
                    <h4 class="context-section-title"><mat-icon>call_made</mat-icon> Direct Callers (Impacted)</h4>
                    <mat-accordion>
                       <mat-expansion-panel *ngFor="let node of ctx.direct_callers" class="mat-elevation-z1">
                          <mat-expansion-panel-header>
                             <mat-panel-title style="font-family: monospace; font-weight: 500;">
                                {{ getShortLabel(node.label || node.id) }}
                             </mat-panel-title>
                             <mat-panel-description>
                                {{ node.source_file || node.id }}
                             </mat-panel-description>
                          </mat-expansion-panel-header>
                          <pre class="snippet-block"><code>{{ getSnippetForNode(node.id, ctx.source_snippets) }}</code></pre>
                       </mat-expansion-panel>
                    </mat-accordion>
                 </div>

                 <!-- Direct Callees -->
                 <div *ngIf="ctx.direct_callees?.length > 0" class="context-section">
                    <h4 class="context-section-title"><mat-icon>call_received</mat-icon> Direct Callees (Dependencies)</h4>
                    <mat-accordion>
                       <mat-expansion-panel *ngFor="let node of ctx.direct_callees" class="mat-elevation-z1">
                          <mat-expansion-panel-header>
                             <mat-panel-title style="font-family: monospace; font-weight: 500;">
                                {{ getShortLabel(node.label || node.id) }}
                             </mat-panel-title>
                             <mat-panel-description>
                                {{ node.source_file || node.id }}
                             </mat-panel-description>
                          </mat-expansion-panel-header>
                          <pre class="snippet-block"><code>{{ getSnippetForNode(node.id, ctx.source_snippets) }}</code></pre>
                       </mat-expansion-panel>
                    </mat-accordion>
                 </div>

                 <!-- Related Tests -->
                 <div *ngIf="ctx.related_tests?.length > 0" class="context-section">
                    <h4 class="context-section-title"><mat-icon>bug_report</mat-icon> Related Tests</h4>
                    <mat-accordion>
                       <mat-expansion-panel *ngFor="let node of ctx.related_tests" class="mat-elevation-z1">
                          <mat-expansion-panel-header>
                             <mat-panel-title style="font-family: monospace; font-weight: 500;">
                                {{ getShortLabel(node.label || node.id) }}
                             </mat-panel-title>
                             <mat-panel-description>
                                {{ node.source_file || node.id }}
                             </mat-panel-description>
                          </mat-expansion-panel-header>
                          <pre class="snippet-block"><code>{{ getSnippetForNode(node.id, ctx.source_snippets) }}</code></pre>
                       </mat-expansion-panel>
                    </mat-accordion>
                 </div>
                 
                 <!-- Other Context -->
                 <div *ngIf="ctx.external_dependencies?.length > 0" class="context-section">
                    <h4 class="context-section-title"><mat-icon>public</mat-icon> External Dependencies</h4>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                       <mat-chip *ngFor="let node of ctx.external_dependencies">{{ getShortLabel(node.label || node.id) }}</mat-chip>
                    </div>
                 </div>
              </div>
           </div>
        </mat-tab>



        <!-- Tab 4: Code -->
        <mat-tab label="Code">
           <div class="tab-content-padding" style="background: #fafafa;">
              <div *ngIf="parsedDiff().length === 0" style="padding: 4rem 2rem; text-align: center; color: #666;">
                 <mat-icon style="font-size: 48px; width: 48px; height: 48px; margin-bottom: 1rem; color: #ccc;">code_off</mat-icon>
                 <h2>No Diff Available</h2>
                 <p>Try re-running the review to fetch the latest diff data.</p>
              </div>

              <div *ngFor="let file of parsedDiff()" class="diff-file-container mat-elevation-z1">
                 <div class="diff-file-header">
                    <mat-icon>insert_drive_file</mat-icon>
                    <strong>{{ file.name }}</strong>
                 </div>
                 <div class="diff-file-content">
                    <ng-container *ngFor="let line of file.lines">
                       <div class="diff-line" [ngClass]="'diff-' + line.type">
                          <div class="diff-line-number">{{ line.number || '' }}</div>
                          <div class="diff-line-content">{{ line.content }}</div>
                       </div>
                       <div class="inline-finding" *ngIf="line.findings && line.findings.length > 0">
                          <div *ngFor="let f of line.findings" class="inline-finding-item">
                             <mat-icon color="warn">warning</mat-icon>
                             <div style="flex: 1;">
                               <strong>{{ f.severity | uppercase }}:</strong> {{ f.description }}
                             </div>
                          </div>
                       </div>
                    </ng-container>
                 </div>
              </div>
           </div>
        </mat-tab>
      </mat-tab-group>
      </div>
      <ng-template #processing>
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; gap: 2rem;">
          <h2 style="color: #666; font-weight: 400; text-transform: uppercase; letter-spacing: 2px;">{{ data.pr_metadata.status }}</h2>
        </div>
      </ng-template>
    </ng-container>
    <ng-template #loading>
      <div style="display: flex; justify-content: center; padding: 4rem;">
        <p style="color: #999;">Fetching job data...</p>
      </div>
    </ng-template>
  `,
  styles: [`
    .review-container { padding-bottom: 3rem; }
    .pr-header { margin-bottom: 2rem; }
    .pr-icon { vertical-align: middle; margin-right: 8px; transform: scale(1.5); }
    .pr-meta { color: #666; font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
    .scm-meta { color: #888; font-size: 0.95rem; display: flex; align-items: center; gap: 0.25rem; margin-top: 0.25rem; }
    .scm-meta mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .tab-content-padding { padding: 1.5rem 0; }
    
    .impact-metric {
      flex: 1;
      min-width: 150px;
      padding: 1rem;
      background: #f5f5f5;
      border-radius: 8px;
      text-align: center;
      border-left: 4px solid #ccc;
    }
    .impact-metric .metric-value { font-size: 28px; font-weight: 500; color: #333; }
    .impact-metric .metric-label { font-size: 12px; color: #666; text-transform: uppercase; margin-top: 4px; }
    
    .impact-metric.risk-low { border-left-color: #4caf50; background: #e8f5e9; }
    .impact-metric.risk-medium { border-left-color: #ff9800; background: #fff3e0; }
    .impact-metric.risk-high { border-left-color: #f44336; background: #ffebee; }
    .blast-radius-card { margin-bottom: 2rem; border-left: 4px solid #ff4081; }
    .summary-text { font-size: 1.1rem; line-height: 1.5; padding: 0.5rem 0; }
    
    .tab-content-padding { padding: 2rem 0; }
    .summary-cards-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .summary-card { text-align: center; padding: 1.5rem; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .summary-value { font-size: 3rem; font-weight: 300; line-height: 1; margin-bottom: 0.5rem; color: #1976d2; }
    .summary-label { font-size: 0.85rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }
    
    .graph-drawer-container { height: 600px; width: 100%; border-radius: 8px; background: white; }
    .graph-header { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; border-bottom: 1px solid #eee; }
    .graph-header h3 { margin: 0; }
    .legend { display: flex; gap: 1rem; font-size: 0.9rem; }
    .legend-item { display: flex; align-items: center; gap: 0.25rem; }
    .swatch { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    .swatch.changed { background-color: #008080; } /* Teal */
    .swatch.impacted { background-color: #9e9e9e; } /* Neutral */
    .swatch.risk-high { background-color: #f44336; } /* Red */
    
    .cy-container { width: 100%; height: 440px; min-height: 400px; position: relative; display: block; }
    
    .details-drawer { width: 650px; max-width: 90vw; padding: 1.5rem; box-sizing: border-box; border-left: 1px solid #e0e0e0; box-shadow: -4px 0 16px rgba(0,0,0,0.2); position: fixed !important; top: 0 !important; right: 0 !important; height: 100vh !important; z-index: 9999 !important; }
    .drawer-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
    .drawer-header h3 { margin: 0; }
    .node-finding { margin-top: 1rem; background: #fff3e0; padding: 0.5rem; border-radius: 4px; }
    
    .table-container { background: white; border-radius: 8px; overflow: hidden; }
    .impact-table-container { background: white; border-radius: 8px; overflow: hidden; margin-top: 1rem; border: 1px solid #eee; }
    .full-width-table { width: 100%; }
    .mono { font-family: monospace; color: #555; }
    
    .tree-container { padding: 1rem; overflow-y: auto; max-height: 500px; }
    .tree-parent-node { margin-bottom: 1.5rem; border: 1px solid #eee; border-radius: 8px; padding: 1rem; background: #fafafa; }
    .tree-parent-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 1.1rem; }
    .tree-children { margin-left: 2rem; border-left: 2px solid #e0e0e0; padding-left: 1rem; }
    .tree-child-row { display: flex; align-items: center; padding: 0.4rem 0; border-bottom: 1px dashed #eee; }
    .tree-child-row:last-child { border-bottom: none; }
    .type-badge { font-size: 0.75rem; background: #eee; padding: 2px 6px; border-radius: 4px; color: #666; text-transform: uppercase; }
    .relation-badge { font-size: 0.75rem; background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 4px; font-weight: 500; min-width: 80px; text-align: center; }

    .diff-file-container { background: white; margin: 1rem 2rem 2rem 2rem; border-radius: 6px; overflow: hidden; border: 1px solid #d0d7de; }
    .diff-file-header { background: #f6f8fa; padding: 0.5rem 1rem; border-bottom: 1px solid #d0d7de; display: flex; align-items: center; gap: 0.5rem; font-family: monospace; font-size: 0.9rem; }
    .diff-file-content { font-family: monospace; font-size: 0.85rem; overflow-x: auto; }
    .diff-line { display: flex; line-height: 1.5; }
    .diff-line-number { min-width: 40px; text-align: right; padding: 0 10px; color: #6e7781; user-select: none; border-right: 1px solid #d0d7de; }
    .diff-line-content { white-space: pre; padding-left: 10px; flex: 1; }
    .diff-added { background-color: #e6ffec; }
    .diff-added .diff-line-number { background-color: #ccffd8; border-color: #54a3ff33; }
    .diff-removed { background-color: #ffebe9; }
    .diff-removed .diff-line-number { background-color: #ffdce0; border-color: #ff818233; }
    .diff-chunk { color: #6e7781; background-color: #ddf4ff; }
    .diff-chunk .diff-line-number { background-color: #b6e3ff; }
    .inline-finding { border-top: 1px solid #d0d7de; border-bottom: 1px solid #d0d7de; }
    .inline-finding-item { display: flex; gap: 0.5rem; background: #fff8c5; padding: 0.5rem 1rem; border-left: 4px solid #d73a49; align-items: center; }
  `]
})
export class ReviewsComponent {
  private apiService = inject(ApiService);
  private route = inject(ActivatedRoute);
  
  @ViewChild('cyContainer', { static: false }) cyContainer!: ElementRef;
  @ViewChild('drawer', { static: false }) drawer!: any;

  reviewData = toSignal(
    this.route.paramMap.pipe(
      switchMap(params => {
        const id = params.get('jobId');
        if (id) {
          return timer(0, 5000).pipe(
            switchMap(() => this.apiService.getJobFindings(parseInt(id, 10))),
            takeWhile(data => !data || !data.pr_metadata || (data.pr_metadata.status !== 'completed' && data.pr_metadata.status !== 'completed_publish_failed' && data.pr_metadata.status !== 'failed'), true)
          );
        }
        return of(null);
      })
    )
  );

  groupedFindings = computed(() => {
    const data = this.reviewData();
    if (!data || !data.findings) return [];
    
    const groups: { [path: string]: any[] } = {};
    for (const f of data.findings) {
      const path = f.file_path || 'General';
      if (!groups[path]) groups[path] = [];
      groups[path].push(f);
    }
    
    return Object.keys(groups).map(path => ({
      file_path: path,
      findings: groups[path]
    })).sort((a, b) => a.file_path.localeCompare(b.file_path));
  }); 
  
  parsedDiff = computed(() => {
    const data = this.reviewData();
    if (!data || !data.diff_data) return [];
    
    const files: any[] = [];
    let currentFile: any = null;
    let lineCounter = 1;
    
    const lines = data.diff_data.split('\n');
    for (let line of lines) {
      if (line.startsWith('+++ b/')) {
        currentFile = { name: line.substring(6).trim(), lines: [] };
        files.push(currentFile);
        lineCounter = 1;
      } else if (line.startsWith('--- a/') || line.startsWith('diff --git') || line.startsWith('index ')) {
        continue; // skip
      } else if (line.startsWith('@@ ')) {
        const match = line.match(/@@ \-\\d+(?:,\\d+)? \\+(\\d+)(?:,\\d+)? @@/);
        if (match && match[1]) {
           lineCounter = parseInt(match[1], 10);
        }
        if (currentFile) currentFile.lines.push({ content: line, type: 'chunk' });
      } else if (currentFile) {
        let type = 'context';
        if (line.startsWith('+')) type = 'added';
        else if (line.startsWith('-')) type = 'removed';
        
        const lineNum = type !== 'removed' ? lineCounter++ : null;
        
        const lineFindings: any[] = [];
        if (lineNum !== null && data.findings) {
           for (const f of data.findings) {
              if (f.file_path && currentFile.name.endsWith(f.file_path.split('/').pop()) && f.line_number === lineNum) {
                 lineFindings.push(f);
              }
           }
        }
        
        currentFile.lines.push({ content: line, type, number: lineNum, findings: lineFindings });
      }
    }
    return files;
  });

  displayedColumns: string[] = ['severity', 'category', 'file_path', 'description'];
  
  selectedNode: any = null;
  selectedNodeFindings: any[] = [];
  selectedNodeSnippet: string | null = null;
  selectedNodeExplanation: string | null = null;
  
  onNodeSelect(nodeData: any) {
     this.selectedNode = { data: (key: string) => nodeData[key] || nodeData };
     const data = this.reviewData();
     
     // Find Findings
     const srcFile = nodeData.source_file || nodeData.id;
     this.selectedNodeFindings = [];
     if (data && data.findings && srcFile) {
        this.selectedNodeFindings = data.findings.filter((f: any) => f.file_path && f.file_path.includes(srcFile));
     }
     
     // Find Source Snippet (Milestone 5)
     this.selectedNodeSnippet = null;
     if (data && data.impact_graph_data && data.impact_graph_data.source_snippets) {
        const snippetObj = data.impact_graph_data.source_snippets.find((s: any) => s.node_id === nodeData.id);
        if (snippetObj && snippetObj.content) {
            this.selectedNodeSnippet = snippetObj.content;
        }
     }
     
     // Generate Explanation (Milestone 5)
     this.selectedNodeExplanation = nodeData.included_because || "No explanation available.";
     if (nodeData.potential_impact) {
         this.selectedNodeExplanation += ` Potential Impact: ${nodeData.potential_impact}`;
     }
     
     if (this.drawer) this.drawer.open();
  }
  cy: any = null;
  graphRenderedForJob: number | null = null;
  
  colorMode: 'type' | 'risk' = 'type';
  availableEdgeTypes: string[] = [];
  hiddenEdgeTypes = new Set<string>();

  viewMode: 'graph' | 'tree' | 'table' = 'tree';
  treeData: any[] = [];
  tableEdgesData: any[] = [];
  
  scopeDepth = '1';
  scopeDirection = 'both';
  includeExternal = false;
  
  onScopeChange() {
     // Trigger re-render with new filter rules locally
     const data = this.reviewData();
     if (data && data.impact_graph_data) {
        this.renderGraph(data);
     }
  }
  
  impactSummary = computed(() => {
    const data = this.reviewData();
    if (!data || !data.impact_graph_data || !data.impact_graph_data.nodes) return null;
    
    let changedSymbols = 0;
    let appDependencies = 0;
    let externalDependencies = 0;
    
    for (const node of data.impact_graph_data.nodes) {
      if (node.modified) {
        changedSymbols++;
      } else if (this.isExternal(node)) {
        externalDependencies++;
      } else {
        appDependencies++;
      }
    }
    
    let impactLevel = 'Low';
    if (appDependencies >= 5) impactLevel = 'High';
    else if (appDependencies > 0) impactLevel = 'Medium';
    else if (changedSymbols > 3) impactLevel = 'Medium';
    
    return {
      changedSymbols,
      appDependencies,
      externalDependencies,
      impactLevel
    };
  });

  toggleColorMode(event: any) {
    if (event.value) {
      this.colorMode = event.value;
      const data = this.reviewData();
      if (data && data.impact_graph_data && this.viewMode === 'graph') {
         this.renderGraph(data);
      }
    }
  }
  
  toggleEdgeType(type: string) {
    if (this.hiddenEdgeTypes.has(type)) {
       this.hiddenEdgeTypes.delete(type);
    } else {
       this.hiddenEdgeTypes.add(type);
    }
    const data = this.reviewData();
    if (data && data.impact_graph_data) {
       this.renderGraph(data);
    }
  }

  onViewModeChange() {
    if (this.viewMode === 'graph') {
       setTimeout(() => {
          const data = this.reviewData();
          if (data && data.impact_graph_data) this.renderGraph(data);
       }, 50);
    }
  }

  onTabChange(event: any) {
    if (event.tab.textLabel === 'Blast Radius' && this.viewMode === 'graph') {
       setTimeout(() => {
          const data = this.reviewData();
          if (data && data.impact_graph_data) this.renderGraph(data);
       }, 100);
    }
  }

  getIconForType(type: string): string {
    const t = (type || '').toLowerCase();
    if (t.includes('class')) return 'data_object';
    if (t.includes('function') || t.includes('method') || t.includes('callable')) return 'code';
    if (t.includes('file') || t.includes('module')) return 'insert_drive_file';
    if (t.includes('test')) return 'bug_report';
    return 'category';
  }

  getShortLabel(label: string): string {
    if (!label) return 'Unknown';
    // Split by . or / or \ and take the last segment
    const parts = label.split(/[.\/\\]/);
    return parts[parts.length - 1] || label;
  }

  isExternal(node: any): boolean {
    if (node.external !== undefined) return node.external;
    if (node.is_external !== undefined) return node.is_external;
    // Fallback heuristic: If it doesn't have a source_file, or the source_file doesn't look like a local path, it's probably external
    const file = node.source_file || node.file || node.path;
    if (!file) return true;
    if (file.includes('node_modules') || file.includes('venv') || file.includes('site-packages') || file.includes('framework')) return true;
    return false;
  }

  getNodeType(node: any): string {
    if (node.node_type) return node.node_type.toUpperCase();
    if (node.type) return node.type.toUpperCase();
    if (node._callable_class || node._class) return 'CLASS';
    if (node._callable) return 'FUNCTION';
    if (node.file_type) return 'FILE';
    return 'SYMBOL';
  }

  getNodeColor(type: string): string {
    const t = (type || '').toLowerCase();
    if (t.includes('class')) return '#ffc107'; // yellow
    if (t.includes('function') || t.includes('method') || t.includes('callable')) return '#00bcd4'; // teal
    if (t.includes('file') || t.includes('module')) return '#9c27b0'; // purple
    if (t.includes('test')) return '#4caf50'; // green
    return '#9e9e9e'; // default
  }

  getGithubUrl(filePath: string, pr: any): string {
    if (!pr || !pr.repo_name) return '#';
    let cleanPath = filePath.replace(/_/g, '/');
    if (filePath.includes('.java') || filePath.includes('.ts') || filePath.includes('.py')) {
        cleanPath = filePath;
    }
    return `https://github.com/${pr.repo_name}/blob/${pr.commit_sha}/${cleanPath}`;
  }

  getSnippetForNode(nodeId: string, snippets: any[]): string {
    if (!snippets) return 'No source available';
    const snippet = snippets.find(s => s.node_id === nodeId);
    return snippet && snippet.content ? snippet.content.trim() : 'No source available';
  }

  getSeverityColor(severity: string): string {
    const s = (severity || '').toLowerCase();
    if (s === 'critical') return '#d32f2f'; // Red
    if (s === 'high') return '#f44336'; // Light Red
    if (s === 'medium') return '#ff9800'; // Orange
    if (s === 'low') return '#4caf50'; // Green
    return '#9e9e9e'; // Grey
  }

  ngAfterViewChecked() {
    const data = this.reviewData();
    if (data && data.impact_graph_data && this.cyContainer && this.graphRenderedForJob !== data.pr_metadata?.number) {
      this.graphRenderedForJob = data.pr_metadata?.number;
      // Increased timeout to guarantee Material drawer has fully painted width/height bounding boxes
      setTimeout(() => this.renderGraph(data), 200);
    }
  }

  renderGraph(data: any) {
    if (this.cy) {
      this.cy.destroy();
    }
    
    let graphData = data.impact_graph_data;
    if (typeof graphData === 'string') {
      try {
        graphData = JSON.parse(graphData);
      } catch (e) {
        console.error("Failed to parse impact_graph_data", e);
        graphData = { nodes: [], edges: [] };
      }
    }

    // Safety check: if no nodes, do not render graph
    if (!graphData.nodes || graphData.nodes.length === 0) {
       return;
    }
    
    // Milestone 4: Apply Scope Filters
    let rawNodes = graphData.nodes;
    let rawEdges = graphData.edges || graphData.links || [];
    
    if (!this.includeExternal) {
        rawNodes = rawNodes.filter((n: any) => !this.isExternal(n) || n.modified);
        const validNodeIds = new Set(rawNodes.map((n: any) => n.id));
        rawEdges = rawEdges.filter((e: any) => validNodeIds.has(e.source) && validNodeIds.has(e.target));
    }
    
    if (this.scopeDepth === '0') {
        rawNodes = rawNodes.filter((n: any) => n.modified);
        const validNodeIds = new Set(rawNodes.map((n: any) => n.id));
        rawEdges = rawEdges.filter((e: any) => validNodeIds.has(e.source) && validNodeIds.has(e.target));
    }

    // Extract available edge types if not already populated
    if (this.availableEdgeTypes.length === 0) {
        const typeSet = new Set<string>();
        rawEdges.forEach((e: any) => {
            if (e.type) typeSet.add(e.type);
            else if (e.rel_type) typeSet.add(e.rel_type);
            else if (e.relation) typeSet.add(e.relation);
            else typeSet.add('calls'); // default fallback
        });
        this.availableEdgeTypes = Array.from(typeSet);
    }

    // Map to Vis Network format
    const visNodes = rawNodes.map((n: any) => {
      let color = '#9e9e9e'; // Default Neutral
      
      // Infer type if missing (for Graphify payload compatibility)
      if (!n.type) {
        if (n._callable_class === true) n.type = 'Class';
        else if (n._callable === true) n.type = 'Function';
        else if (n.file_type === "code") n.type = 'File';
        else n.type = 'Node';
      }

      if (this.colorMode === 'risk') {
          if (n.modified) color = '#008080'; // Teal
          const srcFile = n.source_file || n.id;
          const hasFinding = data.findings.some((f: any) => srcFile && f.file_path.includes(srcFile));
          if (hasFinding) color = '#f44336'; // Red
      } else {
          // Color by Type
          const typeStr = (n.type || '').toLowerCase();
          if (n._callable_class === true || typeStr.includes('class')) color = '#ffc107'; // Yellow
          else if (n._callable === true || typeStr.includes('function') || typeStr.includes('method') || typeStr.includes('callable')) color = '#00bcd4'; // Teal
          else if (n.file_type === 'code' || typeStr.includes('file') || typeStr.includes('module')) color = '#9c27b0'; // Purple
          else if (typeStr.includes('test') || (n.label && n.label.toLowerCase().includes('test'))) color = '#4caf50'; // Green
          else color = '#00bcd4'; // default to function teal
      }
      
      return {
        id: n.id,
        label: n.label || n.id,
        color: color,
        font: { color: '#000000', size: 12, background: 'rgba(255,255,255,0.7)' },
        shape: 'dot',
        size: 15,
        data: n // keep original data
      };
    });
    
    // Filter edges by type and direction
    const modifiedNodeIds = new Set(rawNodes.filter((n: any) => n.modified).map((n: any) => n.id));
    
    rawEdges = rawEdges.filter((e: any) => {
       const eType = e.type || e.rel_type || e.relation || 'calls';
       if (this.hiddenEdgeTypes.has(eType)) return false;
       
       if (this.scopeDirection === 'incoming') {
           // Only keep edges pointing TO a modified node
           return modifiedNodeIds.has(e.target);
       } else if (this.scopeDirection === 'outgoing') {
           // Only keep edges originating FROM a modified node
           return modifiedNodeIds.has(e.source);
       }
       return true;
    });

    const visEdges = rawEdges.map((e: any) => {
      const eType = e.type || e.rel_type || e.relation || 'calls';
      return {
        from: e.source,
        to: e.target,
        dashes: e.inferred ? true : false,
        color: '#ccc',
        arrows: 'to',
        label: eType,
        font: { size: 10, align: 'middle' }
      };
    });

    // Populate Tree and Table data
    const nodesById = new Map<string, any>();
    visNodes.forEach((n: any) => nodesById.set(n.id, n));
    
    const tableData: any[] = [];
    rawEdges.forEach((e: any) => {
       const sourceNode = nodesById.get(e.source);
       const targetNode = nodesById.get(e.target);
       if (sourceNode && targetNode) {
          tableData.push({
             sourceName: sourceNode.label,
             targetName: targetNode.label,
             relation: e.type || e.rel_type || e.relation || 'calls'
          });
       }
    });
    this.tableEdgesData = tableData;

    // Group tree by modified nodes
    const treeBuilder: any[] = [];
    visNodes.forEach((n: any) => {
       if (n.data.modified) {
          const children: any[] = [];
          
          // Find outgoing edges
          rawEdges.filter((e: any) => e.source === n.id).forEach((e: any) => {
             const targetNode = nodesById.get(e.target);
             if (targetNode) {
                children.push({
                   label: targetNode.label,
                   type: targetNode.data.type,
                   relation: e.type || e.rel_type || e.relation || 'calls',
                   originalNode: targetNode.data
                });
             }
          });
          
          // Find incoming edges
          rawEdges.filter((e: any) => e.target === n.id).forEach((e: any) => {
             const sourceNode = nodesById.get(e.source);
             if (sourceNode) {
                children.push({
                   label: sourceNode.label,
                   type: sourceNode.data.type,
                   relation: 'called by / imported by',
                   originalNode: sourceNode.data
                });
             }
          });

          treeBuilder.push({
             label: n.label,
             type: n.data.type,
             modified: true,
             children: children,
             originalNode: n.data
          });
       }
    });
    // If no nodes explicitly marked 'modified', fallback to file nodes as root
    if (treeBuilder.length === 0) {
       visNodes.filter((n: any) => (n.data.type || '').toLowerCase() === 'file').forEach((n: any) => {
          const children: any[] = [];
          rawEdges.filter((e: any) => e.source === n.id || e.target === n.id).forEach((e: any) => {
             const isSrc = e.source === n.id;
             const otherId = isSrc ? e.target : e.source;
             const otherNode = nodesById.get(otherId);
             if (otherNode) {
                children.push({
                   label: otherNode.label,
                   type: otherNode.data.type,
                   relation: isSrc ? (e.type || e.rel_type || e.relation || 'calls') : 'incoming'
                });
             }
          });
          treeBuilder.push({ label: n.label, type: n.data.type, modified: false, children });
       });
    }
    this.treeData = treeBuilder;

    const options = {
      nodes: {
        borderWidth: 1,
        borderColor: '#fff'
      },
      edges: {
        width: 2,
        smooth: {
          enabled: true,
          type: 'cubicBezier',
          forceDirection: 'vertical',
          roundness: 0.4
        }
      },
      layout: {
        hierarchical: {
          direction: 'UD',
          sortMethod: 'directed',
          nodeSpacing: 250,
          levelSeparation: 200
        }
      },
      physics: {
        hierarchicalRepulsion: {
          nodeDistance: 250,
          springLength: 150
        }
      }
    };

    this.cy = new Network(this.cyContainer.nativeElement, { nodes: visNodes, edges: visEdges }, options);

    this.cy.on('click', (params: any) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const selected = visNodes.find((n: any) => n.id === nodeId);
        if (selected) {
           this.onNodeSelect(selected.data);
        }
      }
    });
  }
}
